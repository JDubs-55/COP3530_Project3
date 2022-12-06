#!/usr/bin/env python
from contextlib import asynccontextmanager
import logging
import os
from typing import Optional
import json
from fastapi import FastAPI
from neo4j import (
    basic_auth,
    AsyncGraphDatabase,
)

from starlette.responses import FileResponse
import config
import algos



PATH = os.path.dirname(os.path.abspath(__file__))

##Create Server app on the backend. 
app = FastAPI()


##You have to create a config file with these values
url = os.getenv("NEO4J_URI", config.connectionURI)
username = os.getenv("NEO4J_USER", config.username)
password = os.getenv("NEO4J_PASSWORD", config.password)
neo4j_version = os.getenv("NEO4J_VERSION", config.neo4j_ver) #=5
database = os.getenv("NEO4J_DATABASE", config.database_name) # = neo4j

#Start on this port.
port = os.getenv("PORT", 8080)

##Driver for Neo4j Database queries. 
driver = AsyncGraphDatabase.driver(url, auth=basic_auth(username, password))


@asynccontextmanager
async def get_db():
    if neo4j_version >= "4":
        async with driver.session(database=database) as session_:
            yield session_
    else:
        async with driver.session() as session_:
            yield session_


##Serve index.html
@app.get("/")
async def get_index():
    return FileResponse(os.path.join(PATH, "static", "index.html"))


#Use to populate dropdown
@app.get("/allreportercountries")
async def allReporterCountries():

    async def work(tx):

        result = await tx.run(
            "MATCH (r:Reporter) "
            "RETURN r.REPORTERNAME AS reporter "
        )
        return [record_ async for record_ in result]

    async with get_db() as db:
        results = await db.execute_read(work)
        
    #Get all the reporter country names in a list. 
    reporterNames = []
    for reporter in results:
        reporterNames.append(reporter["reporter"])

    return {"reporterNames":reporterNames}


#Use to populate dropdown for partner countries
@app.get("/allpartnercountries")
async def allPartnerCountries():

    async def work(tx):

        result = await tx.run(
            "MATCH (p:Partner) "
            "RETURN p.PARTNERNAME AS partner "
        )
        return [record_ async for record_ in result]

    async with get_db() as db:
        results = await db.execute_read(work)

    #Get all the partner country names in a list. 
    partnerNames = []
    for partner in results:
        partnerNames.append({"value": partner["partner"], "label": partner["partner"]})

    return {"partnerNames":partnerNames}


#Used to populate product dropdown
@app.get("/allproducts")
async def allProducts():

    async def work(tx):

        result = await tx.run(
            "MATCH (p:Product) "
            "RETURN p.PRODUCTDESCRIPTION AS product "
        )
        return [record_ async for record_ in result]

    async with get_db() as db:
        results = await db.execute_read(work)
        
    ##Get all the product names in a list. 
    productNames = []
    for product in results:
        productNames.append({"value": product["product"], "label":product["product"]})

    return {"productNames":productNames}


#Get all the climate data to match. 
@app.get("/allclimatedata")
async def allTemps():
    async def work(tx):

        result = await tx.run(
            "MATCH (c:CountryW)"
            "RETURN c.Country as countryName, c.Difference as targetTemp"
        )
        return [record_ async for record_ in result]

    async with get_db() as db:
        results = await db.execute_read(work)
        

    temps = {}
    for record in results:
        temps[record["countryName"]] = record["targetTemp"]

    res = json.dumps({"tempData":temps})
    return res



##The big one, this is returning nodes for the reporter, each product type selected, and each partner selected.
##This is specifically formatted to provide input to graph visualization
@app.get("/countrygraph")
async def get_graph(q: Optional[str] = None):

    ##Define query here. q_ are parameters passed through api
    async def work(tx, q_):

        #Params for db query
        data = json.loads(q_)
        reporterName = data["reporterName"]
        productDescription = data["productName"]
        partnerList = data["partnerNames"]

        #Cypher query to retrieve reporter country, product description, and partner country data from graph db looking 
        result = await tx.run(
            "MATCH (r:Reporter {REPORTERNAME: $reporterName})-[:`1988_Traded`]->()-[:`commodity_1988`]->(prod:Product)-[:Export]->(p:Partner) "
            "WHERE prod.PRODUCTDESCRIPTION IN $prodDesc AND p.PARTNERNAME IN $partnerList "
            "RETURN r.REPORTERNAME AS reporter, prod.PRODUCTDESCRIPTION as product, collect(p.PARTNERNAME) as partners ",
            {"reporterName": reporterName, "partnerList": partnerList, "prodDesc":productDescription}
        )
        return [record_ async for record_ in result]

    async with get_db() as db:
        results = await db.execute_read(work,q)
        nodes = []
        links = []

        #Create proper links and nodes for each item
        for record in results:

            if (checkNotDuplicateNode(nodes, record["reporter"])):
                nodes.append({"id": record["reporter"], "group": 0})
            
            if (checkNotDuplicateNode(nodes, record["product"])):
                nodes.append({"id": record["product"], "group":1})
            

            if (checkNotDuplicateLink(links, record["reporter"], record["product"])):
                links.append({"source": record["reporter"], "target": record["product"], "value":1})


            #For each line in the response, there is a list that corresponds to reporter and product, add all
            #The partners as nodes, and a link between product and partner. 
            for item in record["partners"]:
                
                if (checkNotDuplicateNode(nodes, item)):
                    partner = ({"id": item, "group": 2})
                    nodes.append(partner)

                if (checkNotDuplicateLink(links, record["product"], item)):
                    link = {"source": record["product"], "target": item, "value":1}
                    links.append(link)


        #Send data back to caller
        res = json.dumps({"nodes": nodes, "links": links})
        
        return res


## BFS Search API Request
@app.get("/bfsresults")
async def get_bfs(q: Optional[str] = None):

    ##Define query here. q_ are parameters passed through api
    async def work(tx, q_):

        data = json.loads(q_)
        reporterName = data["reporterName"]
        productDescription = data["productName"]
        partnerList = data["partnerNames"]

        #Cypher query to retrieve BFS relevant data for the given selections
        result = await tx.run(
            "MATCH (c:CountryW)-[:match_t]->(r:Reporter {REPORTERNAME: $reporterName})-[:`1988_Traded`]->()-[:`commodity_1988`]->(prod:Product)-[e:Export]->(p:Partner) "
            "WHERE prod.PRODUCTDESCRIPTION IN $prodDesc AND p.PARTNERNAME IN $partnerList "
            "RETURN r.REPORTERNAME AS reporter, prod.PRODUCTDESCRIPTION as product, e.Difference as diff, c.Difference as sourceTemp, COLLECT(distinct p.PARTNERNAME) as partners ",
            {"reporterName": reporterName, "partnerList": partnerList, "prodDesc":productDescription}
        )
        return [record_ async for record_ in result]

    async with get_db() as db:
        results = await db.execute_read(work,q)

        nodes = []
        links = []

        ##Add each reporter, product, partner as nodes, add appropriate links between them
        for record in results:

            if (checkNotDuplicateNode(nodes, record["reporter"])):
                nodes.append({"id": record["reporter"], "group": 0})
            
            if (checkNotDuplicateNode(nodes, record["product"])):
                nodes.append({"id": record["product"], "group":1})
            

            if (checkNotDuplicateLink(links, record["reporter"], record["product"])):
                links.append({"source": record["reporter"], "target": record["product"], "value":-1})

            if (checkNotDuplicateNode(nodes, record["partners"][0])):
                    nodes.append({"id": record["partners"][0], "group": 2})

            if (checkNotDuplicateLink(links, record["product"], record["partners"][0])):

                link = {"source": record["product"], "target": record["partners"][0], "value":1}
                links.append(link)

            #For each line in the response, there is a list that corresponds to reporter and product, add all
            #The partners as nodes, and a link between product and partner. 
            #for item in record["partners"]:
                
                
        #Pass graph data to bfs function. 
        g_data = json.dumps({"nodes": nodes, "links": links})
        sorted_trav = algos.bfsTraversal(g_data)
        sorted_results = organize_results(sorted_trav, results)
        
        #Send BFS sorted objects back to caller. 
        res = json.dumps({"bfsresult":sorted_results})
        
        return res


## DFS Search API Request
@app.get("/dfsresults")
async def get_dfs(q: Optional[str] = None):

    ##Define query here. q_ are parameters passed through api
    async def work(tx, q_):

        #Parse query parameters. 
        data = json.loads(q_)
        reporterName = data["reporterName"]
        productDescription = data["productName"]
        partnerList = data["partnerNames"]

        #Cypher query to get DFS relevant data for the given selection parameters. 
        result = await tx.run(
            "MATCH (c:CountryW)-[:match_t]->(r:Reporter {REPORTERNAME: $reporterName})-[:`1988_Traded`]->()-[:`commodity_1988`]->(prod:Product)-[e:Export]->(p:Partner) "
            "WHERE prod.PRODUCTDESCRIPTION IN $prodDesc AND p.PARTNERNAME IN $partnerList "
            "RETURN r.REPORTERNAME AS reporter, prod.PRODUCTDESCRIPTION as product, e.Difference as diff, c.Difference as sourceTemp, COLLECT(distinct p.PARTNERNAME) as partners ",
            {"reporterName": reporterName, "partnerList": partnerList, "prodDesc":productDescription}
        )
        return [record_ async for record_ in result]

    async with get_db() as db:

        results = await db.execute_read(work,q)
        
        nodes = []
        links = []

        ##Add each reporter, product, and partner as nodes, add appropriate links between them
        for record in results:

            if (checkNotDuplicateNode(nodes, record["reporter"])):
                nodes.append({"id": record["reporter"], "group": 0})
            
            if (checkNotDuplicateNode(nodes, record["product"])):
                nodes.append({"id": record["product"], "group":1})
            

            if (checkNotDuplicateLink(links, record["reporter"], record["product"])):
                links.append({"source": record["reporter"], "target": record["product"], "value":-1})

            if (checkNotDuplicateNode(nodes, record["partners"][0])):
                    nodes.append({"id": record["partners"][0], "group": 2})

            if (checkNotDuplicateLink(links, record["product"], record["partners"][0])):

                link = {"source": record["product"], "target": record["partners"][0], "value":1}
                links.append(link)

            #For each line in the response, there is a list that corresponds to reporter and product, add all
            #The partners as nodes, and a link between product and partner. 
            #for item in record["partners"]:
                
                
        #Run the dfs algo and return a list of sorted edges. 
        g_data = json.dumps({"nodes": nodes, "links": links})
        sorted_trav = algos.dfsTraversal(g_data)

        #Format results for easy use in front end. 
        sorted_results = organize_results(sorted_trav, results) 
        
        #Send data back to caller
        res = json.dumps({"dfsresult":sorted_results})
        return res


#This function formats data recieved from the DFS and BFS algorithms into an easily read array of objects for 
#Use in the frontend. Simplified O(E*E)
def organize_results(ordered_list, records):

    result = []
    reporterSet = []
    productSet = []

    #Get all values of reporter and product. O(E)
    for record in records:
        reporterSet.append(record["reporter"])
        productSet.append(record["product"])

    #Get the set of these lists. 
    reporterSet = list(set(reporterSet))
    productSet = set(productSet)

    #For each tuple received from the Traversal Algorithms
    for tup in ordered_list:

        item = {"from": "...", "through": "...", "to": "...", "diff":"...", "sourceTemp": "...", "partnerTemp":"..."}

        ##If the first tuple is in reporter, this is the root node. and tup[1] is the product node connected to it. 
        ## Set attributes accordingly 
        if (tup[0] in reporterSet and tup[1] in productSet):
            item["from"] = tup[0]
            item["to"] = tup[1]
            result.append(item)
            continue
        
        ##Otherwise we have a Product -> Partner relationship, update list format accordingly 
        elif (tup[0] in productSet):
            item["from"] = reporterSet[0]
            item["through"] = tup[0]
            item["to"] = tup[1]

        #For each record, match the data values to the values already assigned in item
        for record in records: 

            if (record["reporter"]==reporterSet[0] and record["product"]==item["through"] and record["partners"][0]==item["to"]):
                item["diff"] = str(int(record["diff"]*1000)/1000)
                item["sourceTemp"] = str(int(record["sourceTemp"]*1000)/1000)
                break
            
        #Append each item to the result list to be returned. 
        result.append(item)
                
    return result



#Helpers 
# 
#Check that there is not a duplicate node in the nodes list, given a name. O(V) to check duplicate Node
def checkNotDuplicateNode(nodes, name):
    for i in nodes:
        if (i["id"] == name):
            return False

    return True

# Check that there is not a duplicate link in the links list, given a source and target. O(E) to check duplicate Edge
def checkNotDuplicateLink(links, source, target):
    
    for i in links:
        if (i["source"] == source and i["target"] == target):
            return False
    return True

#run
if __name__ == "__main__":
    import uvicorn

    logging.root.setLevel(logging.INFO)
    logging.info("Starting on port %d, database is at %s", port, url)

    uvicorn.run(app, port=port)
