"""
@author: Carmel WENGA
"""

import logging
import re

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from beam_postgres.io import WriteToPostgres


class MyPipelineOptions(PipelineOptions):
    @classmethod
    def _add_argparse_args(cls, parser):
        parser.add_argument('--source')
        parser.add_argument('--target_host')
        parser.add_argument('--target_port')
        parser.add_argument('--db_name')
        parser.add_argument('--table_name')
        parser.add_argument('--username')
        parser.add_argument('--password')


def parse_data(input_str):

    rows = dict()

    for row in re.split('\n', input_str):
        values = re.split(",", row)
        rows.update(
            {
                "age": values[0],
                "gender": values[1],
                "education_level": re.sub("'s", "", values[2]),
                "job_title": values[3],
                "year_of_experience": values[4],
                "salary": values[5]
            }
        )

    return rows


def run(argv=None):

    # Initiate the pipeline using the arguments passed in from the command line.
    pipeline_options = PipelineOptions(argv)
    options = pipeline_options.view_as(MyPipelineOptions)
    p = beam.Pipeline(options=options)

    (p
        # Read the file. This is the source csv files of the pipeline.
        | 'Read from a File' >> beam.io.ReadFromText(options.source, skip_header_lines=1)

        # Convert csv rows to JSON
        | 'CSV to JSON' >> beam.Map(lambda s: parse_data(s))

        # Write data to Postgres
        | 'Write to Postgres' >> WriteToPostgres(
            host=options.target_host,
            database=options.db_name,
            table=options.table_name,
            user=options.username,
            password=options.password,
            port=options.target_port,
            batch_size=1000,
        )
     )
    p.run().wait_until_finish()


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    run()
