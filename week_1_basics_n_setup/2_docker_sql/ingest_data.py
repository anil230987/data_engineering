#!/usr/bin/env python
# coding: utf-8

import pandas as pd
from sqlalchemy import create_engine
from time import time
import argparse
import os

def main(params):
    user=params.user
    password=params.password
    host=params.host
    port=params.port
    db=params.db
    table_name=params.table_name
    url=params.url
    
    csv_name = 'output.csv'
    
    os.system(f"wget {url} -O {csv_name} --no-check-certificate")
    
    #download the csv
    
    engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{db}')

    df = pd.read_csv(csv_name,nrows=100)
    
    df.tpep_pickup_datetime= pd.to_datetime(df.tpep_pickup_datetime)
    df.tpep_dropoff_datetime = pd.to_datetime(df.tpep_dropoff_datetime)
    
    df_iter = pd.read_csv(csv_name,iterator=True,chunksize=100000)
    
    df = next(df_iter)
    
    df.tpep_pickup_datetime= pd.to_datetime(df.tpep_pickup_datetime)
    df.tpep_dropoff_datetime = pd.to_datetime(df.tpep_dropoff_datetime)
    
    df.head(n=0).to_sql(name=table_name,con=engine, if_exists='replace')
    
    df.to_sql(name =table_name, con=engine , if_exists='append')
    
    while True:
        t_start = time()
        df = next(df_iter)
        df.tpep_pickup_datetime= pd.to_datetime(df.tpep_pickup_datetime)
        df.tpep_dropoff_datetime = pd.to_datetime(df.tpep_dropoff_datetime)
        
        df.to_sql(name =table_name, con=engine , if_exists='append')
        
        t_end = time()
        
        print('inserted another chunk.. took %3f seconds '%(t_end-t_start))


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Ingest CSV data to Postgres')
    
    #user , password , port , host database name , table name 
    #URL of csv and 
    
    parser.add_argument('--user',help='user name for postgres')
    parser.add_argument('--password',help='password name for postgres')
    parser.add_argument('--port',help='port name for postgres')
    parser.add_argument('--host',help='host name for postgres')
    parser.add_argument('--db',help='database name for postgres')
    parser.add_argument('--table_name',help='table name where we will write result to')
    parser.add_argument('--url',help='url of csv')
    
    args = parser.parse_args()
    main(args)

