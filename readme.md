# Medi Me

An application specifically for the Hong Kong market that solves the problem of finding the best medical specialist for your problem.
At a glance, it helps you understand:

1. Which type of medical specialist to visit based on the problem you have.
2. Who is the best medical specialist for you.

## Set Up

### Scrape Doctor Data

Run:

```wsl sh
make scrape_overview
make scrape_detail
```

Which pulls data of [HK Licensed Medical Practictioners](https://www.mchk.org.hk/english/list_register/list.php?page=3&ipp=20&type=L)
to local `./data/` folder.

Other sources (not yet scraped):

- [Find Doc](https://www.finddoc.com/en/doctors)
- [See Doctor](https://www.seedoctor.com.hk/dr_detail-1.asp?dr_doctor=2724)
  - Note: Is in Cantonese so would likely need some help on this one
- [WebMD](https://symptoms.webmd.com/)

### Elasticsearch

Docs for Elasticsearch Docker [here](https://www.elastic.co/guide/en/elasticsearch/reference/current/docker.html)

Increase virtual memory first

```powershell
wsl -d docker-desktop
sysctl -w vm.max_map_count=1073741824
```

Then run the following to create a single-node cluster:

```wsl sh
docker network create elastic
docker run --name es01 --net elastic -p 9200:9200 -it docker.elastic.co/elasticsearch/elasticsearch:8.6.2
docker cp es01:/usr/share/elasticsearch/config/certs/http_ca.crt .
curl --cacert http_ca.crt -u elastic https://localhost:9200
```

Then we can run the following to create an index:

```wsl sh
make setup_elastic_index
```

And on future runs; we only need to increase the virtual memory then we can run the container.

```wsl sh
docker start es01
```

### GPT

We will use GPT (text-davinci-003) to help identify medical specialists based on symptoms.
Then based on the symptoms find the best medical specialist.

## Run App

```wsl sh
make run_app
```

### TODO

- Obtain medical problems and their summaries; perhaps on wikipedia. Also can look at medical specialties.
  - Vector embed these with embedding-ada-002

- Then find medical specialists that are related to the medical problem
  - Vector embed these with embedding-ada-002
  - Have a way to map to the problem

For medical specialists; if we find a database; see if we can filter by:
  - Filters on: location, language, price, reviews, complaints, news, etc..
  