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



PATH = os.path.dirname(os.path.abspath(__file__))

app = FastAPI()


##You have to create a config file with these values, I didn't want to post that publicly so i git ignored it. Same as
#The ones you sent me. 
url = os.getenv("NEO4J_URI", config.connectionURI)
username = os.getenv("NEO4J_USER", config.username)
password = os.getenv("NEO4J_PASSWORD", config.password)
neo4j_version = os.getenv("NEO4J_VERSION", config.neo4j_ver) #=5
database = os.getenv("NEO4J_DATABASE", config.database_name) # = neo4j

port = os.getenv("PORT", 8080)

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
        

    reporterNames = []
    for reporter in results:
        reporterNames.append(reporter["reporter"])

    #print(reporterNames)

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

    partnerNames = []
    for partner in results:
        partnerNames.append({"value": partner["partner"], "label": partner["partner"]})

    #print(partnerNames)

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
        

    productNames = []
    for product in results:
        productNames.append({"value": product["product"], "label":product["product"]})

    #print(productNames)
    #print(len(productNames))

    return {"productNames":productNames}




##The big one, this is returning nodes for the reporter, each product type selected, and each partner selected.
##This is specifically formatted to provide input to graph visualization
@app.get("/countrygraph")
async def get_graph(q: Optional[str] = None):

    ##Define query here. q_ are parameters passed through api
    async def work(tx, q_):

        data = json.loads(q_)
        reporterName = data["reporterName"]
        productDescription = data["productName"]
        partnerList = data["partnerNames"]

        # print(reporterName)
        # print(productDescription)
        # print(partnerList)

        result = await tx.run(
            "MATCH (r:Reporter {REPORTERNAME: $reporterName})-[:`1988_Traded`]->()-[:`commodity_1988`]->(prod:Product)-[:Export]->(p:Partner) "
            "WHERE prod.PRODUCTDESCRIPTION IN $prodDesc AND p.PARTNERNAME IN $partnerList "
            "RETURN r.REPORTERNAME AS reporter, prod.PRODUCTDESCRIPTION as product, collect(p.PARTNERNAME) as partners ",
            {"reporterName": reporterName, "partnerList": partnerList, "prodDesc":productDescription}
        )
        return [record_ async for record_ in result]

    async with get_db() as db:
        results = await db.execute_read(work,q)
        # print(results)
        # print(len(results))
        nodes = []
        links = []

        ##Add each reporter and product as nodes, add a link between them
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


        # print(nodes)
        # print(links)

        #This was super touchy, normally you can omitt the json.dumps
        res = json.dumps({"nodes": nodes, "links": links})
        #print(res)

        return res


#Helpers Performance not too bad so i just stuck with brute force. 
def checkNotDuplicateNode(nodes, name):
    for i in nodes:
        if (i["id"] == name):
            return False

    return True

def checkNotDuplicateLink(links, source, target):
    
    for i in links:
        if (i["source"] == source and i["target"] == target):
            return False
    return True




##TEsting/Example
@app.get("/search")
async def get_search(q: Optional[str] = None):
    print("Here")
    print(q)
    async def work(tx, q_):
        print(q_)
        result = await tx.run(
            "MATCH (movie:Movie) "
            "WHERE toLower(movie.title) CONTAINS toLower($title) "
            "RETURN movie", {"title": q_}
        )
        return [record async for record in result]

    if q is None:
        return []
    async with get_db() as db:
        results = await db.execute_read(work, q)
        return [serialize_movie(record["movie"]) for record in results]



#Example Stuff
def serialize_movie(movie):
    return {
        "id": movie["id"],
        "title": movie["title"],
        "summary": movie["summary"],
        "released": movie["released"],
        "duration": movie["duration"],
        "rated": movie["rated"],
        "tagline": movie["tagline"],
        "votes": movie.get("votes", 0)
    }


def serialize_cast(cast):
    return {
        "name": cast[0],
        "job": cast[1],
        "role": cast[2]
    }


# @app.get("/graph")
# async def get_graph(limit: int = 200):
#     async def work(tx):
#         result = await tx.run(
#             "MATCH (m:Movie)<-[:ACTED_IN]-(a:Person) "
#             "RETURN m.title AS movie, collect(a.name) AS cast, ID(m) as identity "
#             "LIMIT $limit",
#             {"limit": limit}
#         )
#         return [record_ async for record_ in result]

#     async with get_db() as db:
#         results = await db.execute_read(work)
#         nodes = []
#         rels = []
#         i = 0
#         for record in results:
#             nodes.append({"title": record["movie"], "label": "movie", "identity":record["identity"]})
#             target = i
#             i += 1
#             for name in record["cast"]:
#                 actor = {"title": name, "label": "actor"}
#                 try:
#                     source = nodes.index(actor)
#                 except ValueError:
#                     nodes.append(actor)
#                     source = i
#                     i += 1
#                 rels.append({"source": source, "target": target})
#         return {"nodes": nodes, "links": rels}


# @app.get("/graphtest")
# async def get_graph(limit: int = 200):
#     async def work(tx):
#         result = await tx.run(
#             "MATCH (m:Movie)<-[:ACTED_IN]-(a:Person) "
#             "RETURN m.title AS movie, collect(a.name) AS cast, ID(m) as identity "
#             "LIMIT $limit",
#             {"limit": limit}
#         )
#         return [record_ async for record_ in result]

#     async with get_db() as db:
#         results = await db.execute_read(work)
#         print(results)
#         nodes = []
#         links = []

#         for record in results:

#             nodes.append({"id": record["movie"], "group": 0,})

#             for name in record["cast"]:
                
#                 if (checkNotPresent(nodes, name)):
#                     actor = ({"id": name, "group":1})
#                     nodes.append(actor)

#                 link = {"source": record["movie"], "target": name, "value":9}
#                 links.append(link)

#         print(nodes)
#         print(links)

#         return {"nodes": nodes, "links": links}



# def checkNotPresent(nodes, name):
#     for i in nodes:
#         if (i["id"] == name):
#             return False

#     return True




# @app.get("/findMovie")
# async def get_search(q: Optional[str] = None):
#     async def work(tx, q_):
#         result = await tx.run(
#             "MATCH (movie:Movie) "
#             "WHERE toLower(movie.title) CONTAINS toLower($title) "
#             "RETURN movie", {"title": q_}
#         )
#         return [record async for record in result]

#     if q is None:
#         return []
#     async with get_db() as db:
#         results = await db.execute_read(work, q)
#         nodes = []
#         rels = []
#         i=0
#         for record in results:
#             nodes.append({"title": record["movie"], "label": "movie"})
#             target = i
#             i += 1
#             for name in record["cast"]:
#                 actor = {"title": name, "label": "actor"}
#                 try:
#                     source = nodes.index(actor)
#                 except ValueError:
#                     nodes.append(actor)
#                     source = i
#                     i += 1
#                 rels.append({"source": source, "target": target})
#         return {"nodes": nodes, "links": rels}


# @app.get("/search2")
# async def get_search(q: Optional[str] = None):
#     async def work(tx, q_):
#         result = await tx.run(
#             "MATCH (movie:Movie) "
#             "WHERE toLower(movie.title) CONTAINS toLower($title) "
#             "RETURN movie", {"title": q_}
#         )
#         return [record async for record in result]

#     if q is None:
#         return []
#     async with get_db() as db:
#         results = await db.execute_read(work, q)
#         return [serialize_movie(record["movie"]) for record in results]


# @app.get("/movie/{title}")
# async def get_movie(title: str):
#     async def work(tx):
#         result_ = await tx.run(
#             "MATCH (movie:Movie {title:$title}) "
#             "OPTIONAL MATCH (movie)<-[r]-(person:Person) "
#             "RETURN movie.title as title,"
#             "COLLECT([person.name, "
#             "HEAD(SPLIT(TOLOWER(TYPE(r)), '_')), r.roles]) AS cast "
#             "LIMIT 1",
#             {"title": title}
#         )
#         return await result_.single()

#     async with get_db() as db:
#         result = await db.execute_read(work)

#         return {"title": result["title"],
#                 "cast": [serialize_cast(member)
#                          for member in result["cast"]]}


# @app.post("/movie/{title}/vote")
# async def vote_in_movie(title: str):
#     async def work(tx):
#         result = await tx.run(
#             "MATCH (m:Movie {title: $title}) "
#             "SET m.votes = coalesce(m.votes, 0) + 1;",
#             {"title": title})
#         return await result.consume()

#     async with get_db() as db:
#         summary = await db.execute_write(work)
#         updates = summary.counters.properties_set

#         return {"updates": updates}


if __name__ == "__main__":
    import uvicorn

    logging.root.setLevel(logging.INFO)
    logging.info("Starting on port %d, database is at %s", port, url)

    uvicorn.run(app, port=port)
