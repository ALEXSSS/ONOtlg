#!/bin/bash

docker run --name mypostgres -p 5433:5432 -e POSTGRES_PASSWORD=pass -d postgres