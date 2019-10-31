#!/bin/bash

# TODO ADD Volume and data save run, (builder-flow)

docker run --name mypostgres -p 5433:5432 -e POSTGRES_PASSWORD=pass -d postgres