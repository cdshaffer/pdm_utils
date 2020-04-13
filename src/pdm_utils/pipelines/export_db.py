"""Pipeline for exporting database information into files."""

from Bio import SeqIO
from Bio.Alphabet import IUPAC
from Bio.SeqFeature import SeqFeature
from Bio.SeqRecord import SeqRecord
from functools import singledispatch
from pathlib import Path
from pdm_utils.classes.alchemyhandler import AlchemyHandler
from pdm_utils.classes.filter import Filter
from pdm_utils.functions import basic
from pdm_utils.functions import flat_files
from pdm_utils.functions import mysqldb
from pdm_utils.functions import parsing
from pdm_utils.functions import querying
from sqlalchemy.sql.elements import Null
from typing import List, Dict
import argparse
import cmd
import copy
import csv
import os
import re
import shutil
import sys
import time

# Valid file formats using Biopython
BIOPYTHON_PIPELINES = ["gb", "fasta", "clustal", "fasta-2line", "nexus",
                       "phylip", "pir", "stockholm", "tab"]
FILTERABLE_PIPELINES = BIOPYTHON_PIPELINES + ["csv"]
PIPELINES = FILTERABLE_PIPELINES + ["sql"]
FLAT_FILE_TABLES = ["phage", "gene"]

#Once trna has data, these tables can be reintroduced.
TABLES = ["phage", "gene", "domain", "gene_domain", "pham",
          #"trna", "tmrna", "trna_structures", 
          "version"]
SEQUENCE_COLUMNS = {"phage"           : ["Sequence"],
                     "gene"            : ["Translation"],
                     "domain"          : [],
                     "gene_domain"     : [],
                     "pham"            : [],
                     "trna"            : ["Sequence"],
                     "tmrna"           : [],
                     "trna_structures" : [],
                     "version"         : []}

# Valid Biopython formats that crash the script due to specific values in
# some genomes that can probably be fixed relatively easily and implemented.
# BIOPYTHON_PIPELINES_FIXABLE = ["embl", "imgt", "seqxml"]
# Biopython formats that are not applicable.
# BIOPYTHON_PIPELINES_INVALID = ["fastq", "fastq-solexa", "fastq-illumina",
#                              "phd", "sff", "qual"]
# Biopython formats that are not writable
# BIOPYTHON_PIPELINES_NOT_WRITABLE = ["ig"]

def main(unparsed_args_list):
    """Uses parsed args to run the entirety of the file export pipeline.

    :param unparsed_args_list: Input a list of command line args.
    :type unparsed_args_list: list[str]
    """
    #Returns after printing appropriate error message from parsing/connecting.
    args = parse_export(unparsed_args_list) 

    alchemist = establish_connection(args.database)
    mysqldb.check_schema_compatibility(alchemist.engine, "export")

    values = []
    filters = []
    groups = []    
    sort = []
    if args.pipeline in FILTERABLE_PIPELINES:
        values = parse_value_list_input(args.input)
        filters = args.filters
        groups = args.groups
        sort = args.sort

    if not args.pipeline in PIPELINES:
        print("ABORTED EXPORT: Unknown pipeline option discrepency.\n"
              "Pipeline parsed from command line args is not supported")
        sys.exit(1)

    if args.pipeline != "I":
        execute_export(alchemist, args.output_path, args.output_name, 
                       args.pipeline, table=args.table, values=values, 
                       filters=filters, groups=groups, sort=sort,
                       include_columns=args.include_columns,
                       exclude_columns=args.exclude_columns,
                       sequence_columns=args.sequence_columns,
                       concatenate=args.concatenate, verbose=args.verbose)
    else:
        pass

def parse_export(unparsed_args_list):
    """Parses export_db arguments and stores them with an argparse object.

    :param unparsed_args_list: Input a list of command line args.
    :type unparsed_args_list: list[str]
    :returns: ArgParse module parsed args.
    """
    EXPORT_SELECT_HELP = """
        Select a export pipeline option to export database data.
            Select csv to export data from a table into a .csv file.
            Select sql to dump the current database into a .sql file.
            Select a formatted file option to export individual entries.
        """
    DATABASE_HELP = "Name of the MySQL database to export from."


    VERBOSE_HELP = """
        Export option that enables progress print statements.
        """
    OUTPUT_PATH_HELP = """
        Export option to change the path
        of the directory where the exported files are stored.
            Follow selection argument with the path to the
            desired export directory.
        """
    OUTPUT_NAME_HELP = """
        Export option to change the name
        of the directory where the exported files are stored.
            Follow selection argument with the desired name.
        """


    IMPORT_FILE_HELP = """
        Selection input option that imports values from a csv file.
            Follow selection argument with path to the
            csv file containing the names of each genome in the first column.
        """
    SINGLE_GENOMES_HELP = """
        Selection input option that imports values from cmd line input.
            Follow selection argument with space separated
            names of genomes in the database.
        """
    TABLE_HELP = """
        Selection option that changes the table in the database selected from.
            Follow selection argument with a valid table from the database.
        """
    FILTERS_HELP = """
        Data filtering option that filters data by the inputted expressions.
            Follow selection argument with formatted filter expression:
                {Table}.{Column}={Value}
        """
    GROUPS_HELP = """
        Data selection option that groups data by the inputted columns.
            Follow selection argument with formatted column expressions:
                {Table}.{Column}={Value}
        """
    SORT_HELP = """
        Data selection option that sorts data by the inputted columns.
            Follow selection argument with formatted column expressions:
                {Table}.{Column}={Value}
        """


    CONCATENATE_HELP = """
        SeqRecord export option to toggle concatenation of files.
            Toggle to enable concatenation of files.
        """


    SEQUENCE_COLUMNS_HELP = """
        Csv export option to toggle removal of sequence-based data.
            Toggle to include sequence based data.
        """
    INCLUDE_COLUMNS_HELP = """
        Csv export option to add additional columns of a database
        to an exported csv file.
            Follow selection argument with formatted column expressions:
                {Table}.{Column}={Value}
        """
    EXCLUDE_COLUMNS_HELP = """
        Csv export option to exclude select columns of a database
        from an exported csv file.
            Follow selection argument with formatted column expressions:
                {Table}.{Column}={Value}
        """
 
    initial_parser = argparse.ArgumentParser()
    initial_parser.add_argument("database", type=str, help=DATABASE_HELP)

    initial_parser.add_argument("pipeline", type=str, choices=PIPELINES,
                               help=EXPORT_SELECT_HELP)

    initial = initial_parser.parse_args(unparsed_args_list[2:4])
  
    optional_parser = argparse.ArgumentParser()

    optional_parser.add_argument("-o", "--output_name", 
                               type=str, help=OUTPUT_NAME_HELP)
    optional_parser.add_argument("-p", "--output_path", type=convert_dir_path,
                               help=OUTPUT_PATH_HELP)
    optional_parser.add_argument("-v", "--verbose", action="store_true",
                               help=VERBOSE_HELP)


    if initial.pipeline in (BIOPYTHON_PIPELINES + ["csv"]):
        table_choices = dict.fromkeys(BIOPYTHON_PIPELINES, FLAT_FILE_TABLES)
        table_choices.update({"csv": TABLES})
        optional_parser.add_argument("-t", "--table", help=TABLE_HELP,
                                choices=table_choices[initial.pipeline])

        optional_parser.add_argument("-if", "--import_file", 
                                type=convert_file_path,
                                help=IMPORT_FILE_HELP, dest="input",
                                default=[])
        optional_parser.add_argument("-in", "--import_names", nargs="*",
                                help=SINGLE_GENOMES_HELP, dest="input")
        optional_parser.add_argument("-f", "--filter", nargs="?",
                                type=parsing.parse_cmd_string,
                                help=FILTERS_HELP,
                                dest="filters")
        optional_parser.add_argument("-g", "--group", nargs="*",
                                help=GROUPS_HELP,
                                dest="groups")
        optional_parser.add_argument("-s", "--sort", nargs="*",
                                help=SORT_HELP)

        if initial.pipeline in BIOPYTHON_PIPELINES:
            optional_parser.add_argument("-cc", "--concatenate",
                                help=CONCATENATE_HELP, action="store_true")
        else:
            optional_parser.add_argument("-sc", "--sequence_columns",
                                help=SEQUENCE_COLUMNS_HELP, action="store_true")
            optional_parser.add_argument("-ic", "--include_columns", nargs="*",
                                help=INCLUDE_COLUMNS_HELP)
            optional_parser.add_argument("-ec", "--exclude_columns", nargs="*",
                                help=EXCLUDE_COLUMNS_HELP)

    date = time.strftime("%Y%m%d")
    default_folder_name = f"{date}_export"
    default_folder_path = Path.cwd()

    optional_parser.set_defaults(pipeline=initial.pipeline, 
                                 database=initial.database,
                                 output_name=default_folder_name,
                                 output_path=default_folder_path,
                                 verbose=False, input=[],
                                 table="phage", filters=[], groups=[], sort=[],
                                 include_columns=[], exclude_columns=[],
                                 sequence_columns=False, concatenate=False)

    parsed_args = optional_parser.parse_args(unparsed_args_list[4:])

    return parsed_args

def execute_export(alchemist, output_path, output_name, pipeline,
                        values=[], verbose=False, table="phage", 
                        filters=[], groups=[], sort=[],
                        include_columns=[], exclude_columns=[], 
                        sequence_columns=False,
                        concatenate=False):
    """Executes the entirety of the file export pipeline.

    :param alchemist: A connected and fully built AlchemyHandler object.
    :type alchemist: AlchemyHandler
    :param output_path: Path to a valid dir for new dir creation.
    :type output_path: Path
    :param output_name: A name for the export folder.
    :type output_name: str
    :param pipeline: File type that dictates data processing.
    :type pipeline: str
    :param values: List of values to filter database results.
    :type values: list[str]
    :param verbose: A boolean value to toggle progress print statements.
    :type verbose: bool
    :param table: MySQL table name.
    :type table: str
    :param filters: A list of lists with filter values, grouped by ORs.
    :type filters: list[list[str]]
    :param groups: A list of supported MySQL column names to group by.
    :type groups: list[str]
    :param sort: A list of supported MySQL column names to sort by.
    :param include_columns: A csv export column selection parameter.
    :type include_columns: list[str]
    :param exclude_columns: A csv export column selection parameter.
    :type exclude_columns: list[str]
    :param sequence_columns: A boolean to toggle inclusion of sequence data.
    :type sequence_columns: bool 
    :param concatenate: A boolean to toggle concaternation for SeqRecords.
    :type concaternate: bool
    """
    if verbose:
        print("Retrieving database version...")
    db_version = mysqldb.get_version_table_data(alchemist.engine)
    
    if pipeline == "csv":
        if verbose:
            print("Processing columns for csv export...")
        csv_columns = get_csv_columns(alchemist, table, 
                                      include_columns=include_columns,
                                      exclude_columns=exclude_columns,
                                      sequence_columns=sequence_columns)

    if pipeline in FILTERABLE_PIPELINES:
        if verbose:
            print("Processing columns for sorting...")
        sort_columns = get_sort_columns(alchemist, sort)
        db_filter = apply_filters(alchemist, table, filters, verbose=verbose)

    if verbose:
        print("Creating export folder...")
    export_path = output_path.joinpath(output_name)
    export_path = basic.make_new_dir(output_path, export_path, attempt=50)

    if pipeline == "sql":
        if verbose:
            print("Writing SQL database file...")
        write_database(alchemist, db_version["Version"], export_path)

    elif pipeline in FILTERABLE_PIPELINES: 
        conditionals_map = {}
        if groups:
            if verbose:
                print("Starting grouping process...")
            build_groups_map(db_filter, export_path, groups=groups,
                                        conditionals_map=conditionals_map,
                                        verbose=verbose)
        else:
            conditionals_map.update({export_path : \
                                        db_filter.build_where_clauses()})
 
        if verbose:
            print("Prepared query and path structure, beginning export...")
        for mapped_path in conditionals_map.keys():
            conditionals = conditionals_map[mapped_path]
            
            if pipeline in BIOPYTHON_PIPELINES:
                execute_ffx_export(alchemist, mapped_path, export_path,
                                   pipeline, db_version, 
                                   table=table, sort=sort_columns,
                                   conditionals=conditionals, values=values,
                                   concatenate=concatenate, verbose=verbose)
            else: 
                execute_csv_export(alchemist, mapped_path, export_path, 
                                   csv_columns, table=table, 
                                   sort=sort_columns,
                                   conditionals=conditionals, values=values,
                                   verbose=verbose)
    else:
        print("Unrecognized export pipeline, aborting export")
        sys.exit(1) 

def execute_csv_export(alchemist, export_path, output_path, columns,
                                        table="phage", conditionals=None,
                                        sort=[], values=[],
                                        verbose=False):
    """Executes csv export of a MySQL database table with select columns.

    :param alchemist: A connected and fully build AlchemyHandler object.
    :type alchemist: AlchemyHandler
    :param export_path: Path to a dir for file creation.
    :type export_path: Path
    :param output_path: Path to a top-level dir.
    :type output_path: Path
    :param table: MySQL table name.
    :type table: str
    :param conditionals: MySQL WHERE clause-related SQLAlchemy objects.
    :type conditionals: list[BinaryExpression]
    :param sort: A list of SQLAlchemy Columns to sort by.
    :type sort: list[Column]
    :param values: List of values to fitler database results.
    :type values: list[str]
    :param verbose: A boolean value to toggle progress print statements.
    :type verbose: bool
    """
    table_obj = querying.get_table(alchemist.metadata, table) 
    primary_key = list(table_obj.primary_key.columns)[0]
    
    if verbose:
        relative_path = str(export_path.relative_to(output_path))
        print(f"Preparing {table} export for '{relative_path}'...")
    
    headers = [primary_key.name]
    for column in columns:
        if column.name != primary_key.name:
            headers.append(column.name)

    query = querying.build_select(alchemist.graph, columns, where=conditionals,
                                                            order_by=sort)
    
    if values:
        results = querying.execute_value_subqueries(alchemist.engine, query,
                                                    primary_key, values)
    else:
        results = alchemist.execute(query)
   
    if len(results) == 0:
        if verbose:
            print(f"No database entries received for '{export_path.name}'.")
        export_path.rmdir() 

    else:
        if verbose:
            print(f"...Writing csv '{export_path.name}.csv'...")
            print("......Database entries retrieved: {len(results)}")

        file_path = export_path.joinpath(f"{export_path.name}.csv")
        basic.export_data_dict(results, file_path, headers,
                                               include_headers=True)

def execute_ffx_export(alchemist, export_path, output_path,
                       file_format, db_version, table="phage", 
                       values=[], conditionals=None, sort=[],
                       concatenate=False, verbose=False): 
    """Executes SeqRecord export of the compilation of data from a MySQL emtry.

    :param alchemist: A connected and fully build AlchemyHandler object.
    :type alchemist: AlchemyHandler
    :param export_path: Path to a dir for file creation.
    :type export_path: Path
    :param output_path: Path to a top-level dir.
    :type output_path: Path
    :param file_format: Biopython supported file type.
    :type file_format: str
    :param db_version: Dictionary containing database version information.
    :type db_version: dict
    :param table: MySQL table name.
    :type table: str
    :param values: List of values to fitler database results.
    :type values: list[str]
    :param conditionals: MySQL WHERE clause-related SQLAlchemy objects.
    :type conditionals: list[BinaryExpression] 
    :param sort: A list of SQLAlchemy Columns to sort by.
    :type sort: list[Column]
    :param concatenate: A boolean to toggle concatenation of SeqRecords.
    :type concaternate: bool
    :param verbose: A boolean value to toggle progress print statements.
    :type verbose: bool
    """
    if verbose:
        print(f"Retrieving {export_path.name} data...")
   
    table_obj = querying.get_table(alchemist.metadata, table)
    primary_key = list(table_obj.primary_key.columns)[0]

    query = querying.build_distinct(alchemist.graph, primary_key,
                                                     where=conditionals,
                                                     order_by=sort)
    if values:
        values = querying.first_column_value_subqueries(alchemist.engine, 
                                                        query, primary_key, 
                                                        values)
    else:
        values = alchemist.first_column(query)

    if len(values) == 0:
        if verbose:
            print(f"No database entries received for '{export_path.name}'.")
        export_path.rmdir()
        return

    if verbose:
        print(f"...Database entries retrieved: {len(values)}")
    seqrecords = []
    if table == "phage": 
        seqrecords = parse_genome_seqrecord_data(alchemist, values=values,
                                                            verbose=verbose)
    elif table == "gene":
        seqrecords = parse_cds_seqrecord_data(alchemist, values=values,
                                                         where=conditionals,
                                                         verbose=verbose)
    else:
        print(f"Unknown error occured, table '{table}' is not recognized "
               "for SeqRecord export pipelines.")
        sys.exit(1)

    if verbose:
            print("Appending database version...")
    for record in seqrecords:
        append_database_version(record, db_version)
    write_seqrecord(seqrecords, file_format, export_path, verbose=verbose,
                                                    concatenate=concatenate)

def parse_genome_seqrecord_data(alchemist, values=[], verbose=False):
    genomes = mysqldb.parse_genome_data(alchemist.engine,
                                        phage_id_list=values,
                                        phage_query="SELECT * FROM phage",
                                        gene_query="SELECT * FROM gene")
    
    seqrecords = []
    for gnm in genomes:
        set_genome_cds_seqfeatures(gnm)
        if verbose:
            print(f"Converting {gnm.name}...")
        seqrecords.append(flat_files.genome_to_seqrecord(gnm))    

    return seqrecords

def retrieve_cds_seqrecord_data(alchemist, values=[], where=[]):
    gene_table = querying.get_table(alchemist.metadata, "gene")
    primary_key = list(gene_table.primary_key.columns)[0]

    cds_data_columns = list(gene_table.c)
    cds_data_columns.append(querying.get_column(alchemist.metadata, 
                                                "phage.HostGenus"))
    cds_data_columns.append(querying.get_column(alchemist.metadata,
                                                "phage.Accession"))
    cds_data_columns.append(querying.get_column(alchemist.metadata,
                                                "phage.DateLastModified"))
    cds_data_columns.append(querying.get_column(alchemist.metadata,
                                                "phage.Length").label(
                                                "PhageLength"))
    
    cds_data_query = querying.build_select(alchemist.graph, cds_data_columns,
                                           where=where)
    if values:
        cds_data = querying.execute_value_subqueries(alchemist.engine,
                                                     cds_data_query, 
                                                     primary_key,
                                                     values)
    else:
        cds_data = querying.execute(alchemist.engine, cds_data_query)

    return cds_data

def parse_cds_seqrecord_data(alchemist, values=[], where=[], verbose=False):
    cds_data_dicts = retrieve_cds_seqrecord_data(alchemist, values=values, 
                                                            where=where)

    seqrecords = []
    for cds_dict in cds_data_dicts:
        cds = mysqldb.parse_gene_table_data(cds_dict)
        cds.genome_length = int(cds_dict["PhageLength"]) 

        if verbose:
            print(f"Converting {cds.id}...")
        record = SeqRecord(cds.translation)
        record.seq.alphabet = IUPAC.IUPACAmbiguousDNA()
        record.name = cds.id
        if cds.locus_tag != "":
            record.id = cds.locus_tag

        cds.set_seqfeature()
        record.features = [cds.seqfeature]

        record.description = get_cds_seqrecord_description(cds_dict)
        record.annotations = get_cds_seqrecord_annotations(cds_dict)
        
        seqrecords.append(record)

    return seqrecords

def write_seqrecord(seqrecord_list, file_format, export_path, concatenate=False,
                                                              verbose=False):
    """Outputs files with a particuar format from a SeqRecord list.

    :param seq_record_list: List of populated SeqRecords.
    :type seq_record_list: list[SeqRecord]
    :param file_format: Biopython supported file type.
    :type file_format: str
    :param export_path: Path to a dir for file creation.
    :type export_path: Path
    :param concatenate: A boolean to toggle concatenation of SeqRecords.
    :type concaternate: bool
    :param verbose: A boolean value to toggle progress print statements.
    :type verbose: bool
    """
    if verbose:
        print("Writing selected data to files...")
    
    record_dictionary = {}
    if concatenate:
        record_dictionary.update({export_path.name:seqrecord_list})
    else:
        for record in seqrecord_list:
            record_dictionary.update({record.name:record})

    for record_name in record_dictionary.keys():
        if verbose:
            print(f"...Writing {record_name}...")
        file_name = f"{record_name}.{file_format}"
        file_path = export_path.joinpath(file_name)
        file_handle = file_path.open(mode='w')
        SeqIO.write(record_dictionary[record_name], file_handle, file_format)
        file_handle.close()

def write_database(alchemist, version, export_path):
    """Output *.sql file from the selected database.

    :param alchemist: A connected and fully built AlchemyHandler object.
    :type alchemist: AlchemyHandler
    :param version: Database version information.
    :type version: int
    :param export_path: Path to a valid dir for file creation.
    :type export_path: Path
    """
    sql_path = export_path.joinpath(f"{alchemist.database}.sql")
    os.system(f"mysqldump -u {alchemist.username} -p{alchemist.password} "
              f"--skip-comments {alchemist.database} > {str(sql_path)}")
    version_path = sql_path.with_name(f"{alchemist.database}.version")
    version_path.touch()
    version_path.write_text(f"{version}")

def establish_connection(database):
    """Establishes a connection to a MySQL database using an AlchemyHandler.

    :param database: Name of a MySQL database.
    :type database: str 
    """
    alchemist = AlchemyHandler()

    alchemist.database = database
    try:
        alchemist.connect(login_attempts=3)
    except ValueError:
        print("Credentials invalid. "
              "Please check your MySQL credentials and try again.")
        sys.exit(1)
    except:
        print("Unknown error occured when logging into MySQL.")
        raise

    try:
        alchemist.connect(ask_database=True, login_attempts=0)
    except ValueError:
        print("Please check your MySQL database access, "
              "and/or your database availability.\n"
             f"Unable to connect to database '{database}' "
              "with valid credentials.")
        sys.exit(1)
    except:
        print("Unknown error occured when connecting to MySQL database.")
        raise
    
    alchemist.build_graph()
    return alchemist 

def apply_filters(alchemist, table, filters, values=None,
                                                     verbose=False):
    """Applies MySQL WHERE clause filters using a Filter.

    :param alchemist: A connected and fully built AlchemyHandler object.
    :type alchemist: AlchemyHandler
    :param table: MySQL table name.
    :type table: str
    :param filters: A list of lists with filter values, grouped by ORs.
    :type filters: list[list[str]]
    :param groups: A list of supported MySQL column names.
    :type groups: list[str]
    :returns: filter-Loaded Filter object.
    :rtype: Filter
    """
    table_obj = alchemist.get_table(table) 
    primary_key = list(table_obj.primary_key.columns)[0]

    db_filter = Filter(alchemist=alchemist, key=primary_key)
    db_filter.values = values

    if verbose:
        print("Processing and building filters...")
    for or_filters in filters:
        for filter in or_filters:
            try:
                db_filter.add(filter)
            except:
                print("Error occured while processing filters.")
                print(f"Filter '{filter}' is not a valid filter.")
                sys.exit(1) 

    db_filter.values = values
    return db_filter

def build_groups_map(db_filter, export_path, groups=[], conditionals_map={},
                                                       verbose=False,
                                                       previous=None,
                                                       depth=0): 
    """Recursive function that generates conditionals and maps them to a Path.
    
    :param db_filter: A connected and fully loaded Filter object.
    :type db_filter: Filter
    :param export_path: Path to a dir for new dir creation.
    :type output_path: Path
    :param groups: A list of supported MySQL column names.
    :type groups: list[str]
    :param conditionals_map: A mapping between group conditionals and Paths.
    :type conditionals_map: dict{Path:list}\
    :param verbose: A boolean value to toggle progress print statements.
    :type verbose: bool
    :param previous: Value set by function to provide info for print statements.
    :type previous: str
    :param depth: Value set by function to provide info for print statements.
    :type depth: int
    :returns conditionals_map: A mapping between group conditionals and Paths.
    :rtype: dict{Path:list}
    """
    groups = groups.copy()
    current_group = groups.pop(0)
    if verbose:
        if depth > 0:
            dots = ".." * depth
            print(f"{dots}Grouping by {current_group} in {previous}...") 
        else:
            print(f"Grouping by {current_group}...")
    
    try:
        group_column = db_filter.convert_column_input(current_group)
    except:
        print(f"Group '{current_group}' is not a valid group.")
        sys.exit(1)
    
    transposed_values = db_filter.build_values(column=current_group,
                                        where=db_filter.build_where_clauses())

    if not transposed_values:
        export_path.rmdir() 
    
    for group in transposed_values:
        group_path = export_path.joinpath(str(group))
        group_path.mkdir() 
        db_filter_copy = db_filter.copy()
        db_filter_copy.add(f"{current_group}={group}")

        if groups:
            previous = f"{current_group} {group}"
            build_groups_map(db_filter_copy, group_path, groups=groups,
                                                    conditionals_map=\
                                                            conditionals_map,
                                                    verbose=verbose,
                                                    previous=previous,
                                                    depth=depth+1)
        else:
            previous = f"{current_group} {group}"
            conditionals_map.update({group_path : \
                                        db_filter_copy.build_where_clauses()})

def get_sort_columns(alchemist, sort_inputs):
    """Function that converts input for sorting to SQLAlchemy Columns.

    :param alchemist: A connected and fully build AlchemyHandler object.
    :type alchemist: AlchemyHandler
    :param sort_inputs: A list of supported MySQL column names.
    :type sort_inputs: list[str]
    :returns: A list of SQLAlchemy Column objects.
    :rtype: list[Column]
    """
    sort_columns = []
    for sort_input in sort_inputs:
        try:
            sort_column = querying.get_column(alchemist.metadata, sort_input)
        except ValueError:
            print("Error occured while selecting sort columns.")
            print(f"Column inputted, '{sort_input}', is invalid.")
            sys.exit(1)
        finally:
            sort_columns.append(sort_column)

    return sort_columns

def get_csv_columns(alchemist, table, include_columns=[], exclude_columns=[], 
                                                    sequence_columns=False):
    """Function that filters and constructs a list of Columns to select.

    :param alchemist: A connected and fully built AlchemyHandler object.
    :type alchemist: AlchemyHandler
    :param table: MySQL table name.
    :type table: str
    :param include_columns: A list of supported MySQL column names.
    :type include_columns: list[str]
    :param exclude_columns: A list of supported MySQL column names.
    :type exclude_columns: list[str]
    :param sequence_columns: A boolean to toggle inclusion of sequence data.
    :type sequence_columns: bool
    :returns: A list of SQLAlchemy Column objects.
    :rtype: list[Column]
    """
    table_obj = alchemist.metadata.tables[table]
    starting_columns = list(table_obj.columns)
    primary_key = list(table_obj.primary_key.columns)[0]
   
    include_column_objs = starting_columns
    for column in include_columns:
        try:
            column_obj = querying.get_column(alchemist.metadata, column)
        except ValueError:
            print("Error occured while selecting csv columns.")
            print(f"Column inputted, '{column}', is invalid.")
            sys.exit(1)
        finally:
            if column_obj not in include_column_objs:
                include_column_objs.append(column_obj)
  
    sequence_column_objs = []
    if not sequence_columns:
        for sequence_column in SEQUENCE_COLUMNS[table]:
            sequence_column_obj = dict(table_obj.c)[sequence_column]
            sequence_column_objs.append(sequence_column_obj)

    exclude_column_objs = sequence_column_objs
    for column in exclude_columns:
        try:
            column_obj = querying.get_column(alchemist.metadata, column)
        except ValueError:
            print("Error occured while selecting csv columns.")
            print(f"Column inputted, '{column}', is invalid.")
            sys.exit(1)
        finally:
            exclude_column_objs.append(column_obj)
            if column_obj.compare(primary_key):
                print(f"Primary key to {table} cannot be excluded")
                sys.exit(1)

            if column_obj not in exclude_column_objs:
                exclude_column_objs.append(column_obj) 

    columns = []
    for column_obj in include_column_objs:
        if column_obj not in exclude_column_objs:
            columns.append(column_obj) 
        
    return columns

def convert_path(path: str):
    """Function to convert a string to a working Path object.

    :param path: A string to be converted into a Path object.
    :type path: str
    :returns: A Path object converted from the inputed string.
    :rtype: Path
    """
    path_object = Path(path)
    if "~" in path:
        path_object = path_object.expanduser()

    if path_object.exists():
        return path_object
    elif path_object.resolve().exists():
        path_object = path_object.resolve()

    print("String input failed to be converted to a working Path object. \n" 
          "Path may not exist.")
    sys.exit(1)

def convert_dir_path(path: str):
    """Function to convert a string to a working directory Path object.

    :param path: A string to be converted into a Path object.
    :type path: str
    :returns: A Path object converted from the inputed string.
    :rtype: Path
    """
    path_object = convert_path(path)

    if path_object.is_dir():
        return path_object
    else:
        print("Path input required to be a directory "
              "does not direct to a valid directory.")
        sys.exit(1)

def convert_file_path(path: str):
    """Function to convert a string to a working file Path object.

    :param path: A string to be converted into a Path object.
    :type path: str
    :returns: A Path object converted from the inputed string.
    :rtype: Path
    """ 
    path_object = convert_path(path)

    if path_object.is_file():
        return path_object
    else:
        print("Path input required to be a file "
              "does not direct to a valid file.")
        raise ValueError

@singledispatch
def parse_value_list_input(value_list_input):
    """Function to convert values input to a recognized data types.

    :param value_list_input: Values stored in recognized data types.
    :type value_list_input: list[str]
    :type value_list_input: Path
    :returns: List of values to filter database results.
    :rtype: list[str]
    """

    print("Value list input for export is of an unexpected type.")
    sys.exit(1)

@parse_value_list_input.register(Path)
def _(value_list_input):
    value_list = []
    with open(value_list_input, newline = '') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter = ",")
        for name in csv_reader:
            value_list.append(name[0])
    return value_list

@parse_value_list_input.register(list)
def _(value_list_input):
    return value_list_input

def set_genome_cds_seqfeatures(phage_genome):
    """Function that populates the Cds objects of a Genome object.

    :param phage_genome: Genome object to query cds data for.
    :type phage_genome: Genome
    """

    try:
        def _sorting_key(cds_feature): return cds_feature.start
        phage_genome.cds_features.sort(key=_sorting_key)
    except:
        if phage_genome == None:
            raise TypeError
        print("Genome cds features unable to be sorted")
        pass
    for cds_feature in phage_genome.cds_features:
        cds_feature.set_seqfeature()

def append_database_version(genome_seqrecord, version_data):
    """Function that sets a property of a SeqRecord with the database version.

    :param genome_seqrecord: Filled SeqRecord object with relevant attribtues.
    :type genome_seqfeature: SeqRecord
    :param version_data: Dictionary containing database version information.
    :type version_data: dict
    """
    version_keys = version_data.keys()
    if "Version" not in version_keys or "SchemaVersion" not in version_keys:
        raise ValueError("Version of selected database is outdated. "
                         "Version data is incompatable.")
    try:
        genome_seqrecord.annotations["comment"] =\
                genome_seqrecord.annotations["comment"] + (
                    "Database Version: {}; Schema Version: {}".format(
                                        version_data["Version"],
                                        version_data["SchemaVersion"]),)
    except:
        if isinstance(genome_seqrecord, SeqRecord):
            raise ValueError

        elif genome_seqrecord == None:
            raise TypeError
        raise

#PROTOTYPE FUNCTIONS
#--------------------------------------------------------
def get_cds_seqrecord_description(cds_dict):
    cds_product = cds_dict["Notes"].decode("utf-8")
    if cds_product == "":
        cds_product = "hypothetical protein"

    cds_parent = cds_dict["PhageID"]
    parent_host_genus = cds_dict["HostGenus"]

    description = f"{cds_product} [{parent_host_genus} phage {cds_parent}]"
    return description
    
def get_cds_seqrecord_annotations(cds_dict):
    annotations = {"molecule type": "DNA",
                   "topology" : "linear",
                   "data_file_division" : "PHG",
                   "date" : "",
                   "accessions" : [],
                   "sequence_version" : "",
                   "keyword" : [],
                   "source" : "",
                   "organism" : "",
                   "taxonomy" : [],
                   "comment" : ()}
  
    annotations["date"] = cds_dict["DateLastModified"]
    annotations["organism"] = (f"{cds_dict['HostGenus']} phage "
                               f"{cds_dict['PhageID']}")
    annotations["source"] = f"Accession {cds_dict['Accession']}"

    annotations["taxonomy"].append("Viruses")
    annotations["taxonomy"].append("dsDNA Viruses")
    annotations["taxonomy"].append("Caudovirales")

    annotations["comment"] = get_cds_seqrecord_annotations_comments(cds_dict)

    return annotations

def get_cds_seqrecord_annotations_comments(cds_dict):
    pham_comment =\
           f"Pham: {cds_dict['PhamID']}"
    auto_generated_comment =\
            "Auto-generated genome record from a MySQL database"
    
    return (pham_comment, auto_generated_comment)
