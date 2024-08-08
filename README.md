# This repository is now archived.

openfuelservice was a first prototype regarding fuel saving topics and we gained valuable knowledge through it. 
Due to being heavily out-dated and a missing vision for this project, we have to let it go, for now.

If you want to get in touch with us regarding this or other related topics, feel free to contact us under **support[at]smartmobility.heigit.org** or visit us at [heigit.org](https://heigit.org).


---
OLD README
---
## Run as Docker Container (Flask + Gunicorn)
---
#### 1. Requirements
You need `docker` and `docker-compose` installed!
#### 2. Install PostgreSQL-Service with docker
-  Set your desired `postgres_user | postgres_pass and postgres_dbname` --> Remember to adjust those changes in the `ofs_settings_docker.yml` if you don't use the standard values:
```bash
`docker run --name=ofs-postgis -d -e POSTGRES_USER=gis_admin -e POSTGRES_PASS=admin -e POSTGRES_DBNAME=gis -e ALLOW_IP_RANGE=0.0.0.0/0 -p 5434:5432 kartoza/postgis:9.6-2.4`
```
#### 3. Prepare the current brand matching models
- Download the models: `Download link is coming soon`.    
- Prepare the models: Create a folder called `ann_models` in the ofs root folder and copy the models in it.

#### 4. Start OpenFuelService
Run ofs from the root folder:
```bash
docker-compose up -d
```

#### 5. Configure OpenFuelService
-  Create the db:
```bash
docker exec -it container_name /ofs_venv/bin/python manage.py create_db
```
- Import the data:
```bash
docker exec -it container_name /ofs_venv/bin/python manage.py import_data
```
- Match the data (This will take some time):
```bash
docker exec -it container_name /ofs_venv/bin/python manage.py match_data
```
-  If done, ofs should be ready to test. Head to the end of the file to find some test queries.
---
## Manual Setup (Ubuntu and Arch)
---
### Ubuntu Preparations
#### 1. Requirements
-  You need at least `Ubuntu 18.04 with python 3.6!`
-  A freshly created virtual environment (recommended!)
#### 2. Install the required packages
```bash
sudo apt update
sudo apt install python3-distutils  
sudo apt install python3-dev
```


### Arch Preparations
#### 1. Requirements
-  A freshly created virtual environment (recommended!)
-  Install the beautiful `yay` aur manager 
#### 2. Install required packages
```bash  
sudo pacman -S base-devel  
sudo pacman -S postgresql-libs  
sudo pacman -S libyaml  
sudo pacman -S cython  
sudo pacman -S cython2  
sudo pacman -S geos  
yay -S python-distutils  
yay -S python2-distutils  
```   
---
### General steps
#### 3. Activate your venv
#### 4. Install requirements
-  Install the `requirements.txt` from the ofs base folder
```bash
pip install -r requirements.txt   
```
#### 5. Install PostgreSQL-Service with docker
-  Add your desired postgres_user | postgres_pass and postgres_dbname --> Remember to adjust those changes in the `ofs_settings.yml` if you don't use the standard values:
```bash
docker run --name=ofs-postgis -d -e POSTGRES_USER=gis_admin -e POSTGRES_PASS=admin -e POSTGRES_DBNAME=gis -e ALLOW_IP_RANGE=0.0.0.0/0 -p 5434:5432 kartoza/postgis:9.6-2.4
```

#### 6. Prepare the matching models
- Download the models: `Download link is coming soon`.    
- Prepare the models: Copy the models in the `openfuelservice/server/files/models/` folder.

#### 7. Create the database
-  Run the creation process from the root folder of ofs:
```bash
python manage.py create-db   
```
-  `Couldn't drop user gis_admin` and `Couldn't create user gis_admin` can be ignored!

#### 8. Import the data
```bash
python manage.py import-data
```

#### 8. Run the server
```bash
python manage.py run  
```
---
# Test queries
-  Please adjust the curl requests if you changed anything from the standard settings e.g. port and ip from the docker container etc.

###### [GET] Standard data queries:
-   Get supported categories:
```bash
curl -X GET \
  'http://127.0.0.1:5000/fuel?request=categories' \
  -H 'cache-control: no-cache'
```
-   Get currently supported brands:
```bash
curl -X GET \
  'http://127.0.0.1:5000/fuel?request=brands&source=cfd' \
  -H 'cache-control: no-cache'
```
-   Get currently supported cars for `VW`:
```bash
curl -X GET \
  'http://127.0.0.1:5000/fuel?request=cars&brand=VW&source=cfd' \
  -H 'cache-control: no-cache'
```
###### [POST] Route Calculation examples:
-   Query for all categories:
```bash
curl -X POST \
'http://127.0.0.1:5000/fuel?request=route' \
-H 'Content-Type: application/json' \
-H 'cache-control: no-cache' \
-d '{
  "request": "route",
  "geometry": {
    "geojson": {
      "coordinates":  [
      [8.679111522296585, 49.40613104364613],
      [8.679119403627244, 49.40613014781563]
      ],
      "type": "LineString"
    },
    "filters":{
      "data_source": "cfd",
      "fuel_type": "gasoline",
      "vehicle_type": "car",
      "driving_speed": "150",
      "vehicle_categories": ["all"],
      "request_id": "test123"
    }
  }
}'
```
-   Query only category  `b` and `c` and set the `tank_size` and an individual `fuel_consumption` to override ofs values:
```bash
curl -X POST \
'http://127.0.0.1:5000/fuel?request=route' \
-H 'Content-Type: application/json' \
-H 'cache-control: no-cache' \
-d '{
  "request": "route",
  "geometry": {
    "geojson": {
      "coordinates":  [
      [8.679111522296585, 49.40613104364613],
      [8.679119403627244, 49.40613014781563]
      ],
      "type": "LineString"
    },
    "filters":{
      "data_source": "cfd",
      "fuel_type": "gasoline",
      "vehicle_type": "car",
      "driving_speed": "150",
      "vehicle_categories": ["b", "c"],
      "tank_sizes": {"a":"20"},
      "fuel_consumptions": {"a": "4.5"},
      "request_id": "test123"
    }
  }
}'
```

-  Query a specific car from the database. You need to query a hash from the database to paste it in the body (See the example above: `Get currently supported cars for VW `):
```bash
curl -X POST \
  'http://127.0.0.1:5000/fuel?request=route' \
  -H 'Content-Type: application/json' \
  -H 'cache-control: no-cache' \
  -d '{
  "request": "route",
  "geometry": {
    "geojson": {
      "coordinates": [
                    [
                        10.502782,
                        51.181212
                    ],
                    [
                        10.50239,
                        51.1812
                    ],
                    [
                        10.501769,
                        51.181171
                    ]
                ],
                "type": "LineString"
    },
     "filters":{
	  "data_source": "cfd",
      "fuel_type": "gasoline",
      "vehicle_type": "car",
      "driving_speed": "60",	
      "cfd_ids": ["{enter your car id here without the {}}"],
      "request_id": "test123"
    }
  }
}'
```
