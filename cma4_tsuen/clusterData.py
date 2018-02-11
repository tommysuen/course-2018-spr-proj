import urllib.request
import json
import dml
import prov.model
import datetime
import uuid

class hubway(dml.Algorithm):
    contributor = 'charles_tommy'
    reads = ['charles_tommy.entertainment', 'charles_tommy.hubway']
    writes = ['charles_tommy.']

    def dist(p, q):
        (x1,y1) = p
        (x2,y2) = q
        return (x1-x2)**2 + (y1-y2)**2

    def plus(args):
        p = [0,0]
        for (x,y) in args:
            p[0] += x
            p[1] += y
        return tuple(p)

    def scale(p, c):
        (x,y) = p
        return (x/c, y/c)

    @staticmethod
    def execute(trial = False):
        '''Retrieve some data sets (not using the API here for the sake of simplicity).'''
        startTime = datetime.datetime.now()

        # Set up the database connection.
        client = dml.pymongo.MongoClient()
        repo = client.repo
        repo.authenticate('charles_tommy', 'charles_tommy')

        url = 'https://secure.thehubway.com/data/stations.json'
        response = urllib.request.urlopen(url).read().decode("utf-8")
        r = json.loads(response)
        stations = r["stations"]
        s = json.dumps(r, sort_keys=True, indent=2)
        repo.dropCollection("charles_tommy.hubway")
        repo.createCollection("charles_tommy.hubway")
        repo['charles_tommy.hubway'].insert_many(stations)
        repo['charles_tommy.hubway'].metadata({'complete':True})
        print(repo['charles_tommy.hubway'].metadata())

        repo.logout()

        endTime = datetime.datetime.now()

        return {"start":startTime, "end":endTime}
    
    @staticmethod
    def provenance(doc = prov.model.ProvDocument(), startTime = None, endTime = None):
        '''
            Create the provenance document describing everything happening
            in this script. Each run of the script will generate a new
            document describing that invocation event.
            '''

        # Set up the database connection.
        client = dml.pymongo.MongoClient()
        repo = client.repo
        repo.authenticate('charles_tommy', 'charles_tommy')
        doc.add_namespace('alg', 'http://datamechanics.io/algorithm/') # The scripts are in <folder>#<filename> format.
        doc.add_namespace('dat', 'http://datamechanics.io/data/') # The data sets are in <user>#<collection> format.
        doc.add_namespace('ont', 'http://datamechanics.io/ontology#') # 'Extension', 'DataResource', 'DataSet', 'Retrieval', 'Query', or 'Computation'.
        doc.add_namespace('log', 'http://datamechanics.io/log/') # The event log.
        doc.add_namespace('hubway', 'http://bostonopendata-boston.opendata.arcgis.com/datasets/')

        this_script = doc.agent('alg:charles_tommy#hubway', {prov.model.PROV_TYPE:prov.model.PROV['SoftwareAgent'], 'ont:Extension':'py'})
        resource = doc.entity('bdp:wc8w-nujj', {'prov:label':'311, Service Requests', prov.model.PROV_TYPE:'ont:DataResource', 'ont:Extension':'json'})
        get_stations = doc.activity('log:uuid'+str(uuid.uuid4()), startTime, endTime)
        doc.wasAssociatedWith(get_stations, this_script)
        doc.usage(get_stations, resource, startTime, None,
                  {prov.model.PROV_TYPE:'ont:Retrieval'
                  }
                  )

        lost = doc.entity('dat:charles_tommy#hubway', {prov.model.PROV_LABEL:'Hubway Stations', prov.model.PROV_TYPE:'ont:DataSet'})
        doc.wasAttributedTo(hubway, this_script)
        doc.wasGeneratedBy(hubway, get_stations, endTime)
        doc.wasDerivedFrom(hubway, resource, get_stations, get_stations, get_stations)

        repo.logout()
                  
        return doc

hubway.execute()
doc = hubway.provenance()
print(doc.get_provn())
print(json.dumps(json.loads(doc.serialize()), indent=4))

## eof