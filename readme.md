# Medi Me

An application specifically for the Hong Kong market that solves the problem of finding the best medical specialist for your problem.
At a glance, it helps you understand:

1. Which type of medical specialist to visit
2. Who is the best medical specialist for you

We will start by scraping data from websites:

- [HK Licensed Medical Practictioners](https://www.mchk.org.hk/english/list_register/list.php?page=3&ipp=20&type=L)
- [Find Doc](https://www.finddoc.com/en/doctors)
- [See Doctor](https://www.seedoctor.com.hk/dr_detail-1.asp?dr_doctor=2724)
  - Note: Is in Cantonese so would likely need some help on this one

And later:

- [WebMD](https://symptoms.webmd.com/)

## Elasticsearch

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
