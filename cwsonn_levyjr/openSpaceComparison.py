import urllib.request
import json
import dml
import prov.model
import datetime
import uuid
import numpy as np


class openSpaceComparison(dml.Algorithm):
    contributor = 'cwsonn_levyjr'
    reads = ['cwsonn_levyjr.Copenspace', 'cwsonn_levyjr.openspace']
    writes = ['cwsonn_levyjr.openSpaceComparison']
    
    def intersect(R, S):
        return [t for t in R if t in S]

    @staticmethod
    def execute(trial = False):
        '''Retrieve some data sets (not using the API here for the sake of simplicity).'''
        startTime = datetime.datetime.now()

        # Set up the database connection.
        client = dml.pymongo.MongoClient()
        repo = client.repo
        repo.authenticate('cwsonn_levyjr', 'cwsonn_levyjr')

        BopenSpace = repo['cwsonn_levyjr.openspace'].find()

        #Get Boston open space areas
        parkAreasBos = []
        for b in BopenSpace:
            area = b["properties"]["ShapeSTArea"]
            parkAreasBos.append(area)

        CopenSpace = repo['cwsonn_levyjr.Copenspace'].find()

        #Get Cambridge open space areas
        CamAreaTotal = 0
        parkAreasCam = []
        for c in CopenSpace:
            area = c["shape_area"]
            parkAreasCam.append(area)

        #Combine Data
        repo.dropCollection("cwsonn_levyjr.openSpaceComparison")
        repo.createCollection("cwsonn_levyjr.openSpaceComparison")

        park_dict = {'BosOpenSpaces': parkAreasBos, 'CamOpenSpaces': parkAreasCam}
        repo['cwsonn_levyjr.openSpaceComparison'].insert_one(park_dict)
        
        combinedData = repo['cwsonn_levyjr.openSpaceComparison'].find()

        BosAreaTotal = 0
        CamAreaTotal = 0
        for b in combinedData:
            areaB = b["BosOpenSpaces"]
            areaC = b["CamOpenSpaces"]
            x = np.array(areaC)
            areaC = x.astype(np.float)
            
            for i in range(len(areaB)):
                BosAreaTotal += areaB[i]
            for j in range(len(areaC)):
                CamAreaTotal += areaC[j]
    
        areaCount = 0
        for i in range(len(areaB)):
            for j in range(len(areaC)):
                if(areaC[j] - 10 <= areaB[i] <= areaC[j] + 10):
                    areaCount += 1

        bikeAreaTotals = {'BosOpenSpaceAreaTotal': BosAreaTotal, 'CamOpenSpaceAreaTotal': CamAreaTotal}
        bikeIntersectionsTotals = {'IntersectionTotals': areaCount}

        repo['cwsonn_levyjr.openSpaceComparison'].insert_one(bikeAreaTotals)
        repo['cwsonn_levyjr.openSpaceComparison'].insert_one(bikeIntersectionsTotals)


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
        repo.authenticate('cwsonn_levyjr', 'cwsonn_levyjr')
        doc.add_namespace('alg', 'http://datamechanics.io/algorithm/') # The scripts are in <folder>#<filename> format.
        doc.add_namespace('dat', 'http://datamechanics.io/data/') # The data sets are in <user>#<collection> format.
        doc.add_namespace('ont', 'http://datamechanics.io/ontology#') # 'Extension', 'DataResource', 'DataSet', 'Retrieval', 'Query', or 'Computation'.
        doc.add_namespace('log', 'http://datamechanics.io/log/') # The event log.
        doc.add_namespace('bdp', 'https://data.cityofboston.gov/resource/')

        this_script = doc.agent('alg:cwsonn_levyjr#example', {prov.model.PROV_TYPE:prov.model.PROV['SoftwareAgent'], 'ont:Extension':'py'})
        resource = doc.entity('bdp:wc8w-nujj', {'prov:label':'311, Service Requests', prov.model.PROV_TYPE:'ont:DataResource', 'ont:Extension':'json'})
        get_found = doc.activity('log:uuid'+str(uuid.uuid4()), startTime, endTime)
        get_lost = doc.activity('log:uuid'+str(uuid.uuid4()), startTime, endTime)
        doc.wasAssociatedWith(get_found, this_script)
        doc.wasAssociatedWith(get_lost, this_script)
        doc.usage(get_found, resource, startTime, None,
                  {prov.model.PROV_TYPE:'ont:Retrieval',
                  'ont:Query':'?type=Animal+Found&$select=type,latitude,longitude,OPEN_DT'
                  }
                  )
        doc.usage(get_lost, resource, startTime, None,
                  {prov.model.PROV_TYPE:'ont:Retrieval',
                  'ont:Query':'?type=Animal+Lost&$select=type,latitude,longitude,OPEN_DT'
                  }
                  )

        lost = doc.entity('dat:cwsonn_levyjr#lost', {prov.model.PROV_LABEL:'Animals Lost', prov.model.PROV_TYPE:'ont:DataSet'})
        doc.wasAttributedTo(lost, this_script)
        doc.wasGeneratedBy(lost, get_lost, endTime)
        doc.wasDerivedFrom(lost, resource, get_lost, get_lost, get_lost)

        found = doc.entity('dat:cwsonn_levyjr#found', {prov.model.PROV_LABEL:'Animals Found', prov.model.PROV_TYPE:'ont:DataSet'})
        doc.wasAttributedTo(found, this_script)
        doc.wasGeneratedBy(found, get_found, endTime)
        doc.wasDerivedFrom(found, resource, get_found, get_found, get_found)

        repo.logout()
                  
        return doc

openSpaceComparison.execute()
doc = openSpaceComparison.provenance()
print(doc.get_provn())
print(json.dumps(json.loads(doc.serialize()), indent=4))

