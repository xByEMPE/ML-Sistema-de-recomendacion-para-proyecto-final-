bq load --autodetect --source_format=CSV my_dataset.my_table gs://datos_gl_bucket/limpios_estados/*.csv
bq load --autodetect --source_format=CSV datos_gl_bucket/Google Maps/limpios_estados/*.csv
pip install google-cloud-storage
gcloud auth application-default login
