"""Functions to interact with PhagesDB"""


from pipelines.database_import import evaluate
from classes import Genome
from classes import GenomePair
from functions import basic
from constants import constants
import urllib.request
import json
from functions import misc


def parse_phagesdb_phage_name(data_dict):
    """Retrieve Phage Name from PhagesDB."""
    try:
        phage_name = data_dict['phage_name']
    except:
        phage_name = ""
    return phage_name



def parse_phagesdb_cluster(data_dict):
    """Retrieve Cluster from PhagesDB.
    If the phage is clustered, 'pcluster' is a dictionary, and one key is
    the Cluster data (Cluster or 'Singleton').
    If for some reason no Cluster info is added at the time
    the genome is added to PhagesDB, 'pcluster' may automatically be
    set to NULL, which gets converted to "Unclustered" during retrieval.
    In Phamerator NULL means Singleton, and the long form
    "Unclustered" is invalid due to its character length,
    so this value is converted to 'UNK' ('Unknown').
    """

    try:
        if data_dict["pcluster"] is None:
            cluster = 'UNK'
        else:
            cluster = data_dict["pcluster"]["cluster"]
    except:
        cluster = ""
    return cluster


def parse_phagesdb_subcluster(data_dict):
    """Retrieve Subcluster from PhagesDB.
    If for some reason no cluster info is added at the time
    the genome is added to PhagesDB, 'psubcluster' may automatically be
    set to NULL, which gets returned as None.
    If the phage is a Singleton, 'psubcluster' is None.
    If the phage is clustered but not subclustered, 'psubcluster' is None.
    If the phage is clustered and subclustered, 'psubcluster'
    is a dictionary, and one key is the Subcluster data."""

    try:
        if data_dict["psubcluster"] is None:
            subcluster = "none"
        else:
            subcluster = data_dict["psubcluster"]["subcluster"]
    except:
        subcluster = ""
    return subcluster


def parse_phagesdb_host_genus(data_dict):
    """Retrieve host_genus from PhagesDB."""
    try:
        host_genus = data_dict["isolation_host"]["genus"]
    except:
        host_genus = ""
    return host_genus


def parse_phagesdb_accession(data_dict):
    """Retrieve Accession from PhagesDB."""
    try:
        accession = data_dict["genbank_accession"]
    except:
        accession = ""

    return accession



def parse_phagesdb_filename(data_dict):
    """Retrieve fasta filename from PhagesDB."""

    try:
        fastafile_url = data_dict["fasta_file"]
    except:
        fastafile_url = ""
    return fastafile_url


def retrieve_phagesdb_fasta(fastafile_url):
    """Retrieve fasta file from PhagesDB."""

    try:
        request = urllib.request.Request(fastafile_url)
        with urllib.request.urlopen(request) as response:
            fasta_data = response.read()
            fasta_data = fasta_data.decode("utf-8")
    except:
        fasta_data = ""
    return fasta_data




# TODO obsolete, once a biopython-based parser has been built?
def parse_fasta_file(fasta_file):
    """Parses sequence data from a fasta-formatted file.
    """
    # All sequence rows in the fasta file may not have equal widths,
    # so some processing of the data is required. If you split by newline,
    # the header is retained in the first list element.
    split_fasta_data = fasta_file.split('\n')

    header = ""
    sequence = ""

    if len(split_fasta_data) > 1:

        header = split_fasta_data[0]
        if header[0] == ">":
            header = header[1:] # remove '>' symbol.

        header = header.strip() # remove any whitespace
        index = 1
        while index < len(split_fasta_data):

            # Strip off potential whitespace before appending, such as '\r'.
            sequence = sequence + split_fasta_data[index].strip()
            index += 1

    result = (header, sequence)

    return result






# TODO implement
# TODO unit test.
def parse_fasta_file2(fasta_file):
    """Parses sequence data from a fasta-formatted file using Biopython.
    """

    # TODO need to work out whether SeqIO can retrieve the data
    # directly from the server or whether the data needs to be first
    # retrieved and then parsed.
    # Using SeqIO to retrieve a record from PhagesDB server did not work.

    pass



def parse_phagesdb_data(genome_obj,data_dict):
    """Parses a dictionary of genome data retrieved from PhagesDB into a
    Genome object.
    """

    # Phage Name, PhageID and SearchID
    phage_name = parse_phagesdb_phage_name(data_dict)
    genome_obj.name = phage_name
    genome_obj.set_id(phage_name)

    # Host
    host_genus = parse_phagesdb_host_genus(data_dict)
    genome_obj.set_host(host_genus, "empty_string")

    # Accession
    accession = parse_phagesdb_accession(data_dict)
    genome_obj.set_accession(accession, "empty_string")

    # Cluster
    cluster = parse_phagesdb_cluster(data_dict)
    genome_obj.set_cluster(cluster)

    #Subcluster
    subcluster = parse_phagesdb_subcluster(data_dict)
    genome_obj.set_subcluster(subcluster, "empty_string")

    # Fasta file URL
    fastafile_url = parse_phagesdb_filename(data_dict)
    genome_obj.filename = fastafile_url


    # Fasta file record
    if genome_obj.filename != "":
        fasta_file = retrieve_phagesdb_fasta(genome_obj.filename)

        # TODO unit test - not sure how to test this, since this function
        # retrieves and parses files from PhagesDB.
        # Genome sequence and parsed record
        if fasta_file != "":

            fasta_data = parse_fasta_file(fasta_file)
            fasta_record = misc.create_fasta_seqrecord(fasta_data[0], fasta_data[1])
            genome_obj.seq = fasta_record.seq
            genome_obj.description = fasta_record.description
            genome_obj.parse_description()

    genome_obj.type = "phagesdb"

    evaluate.check_phagesdb_genome(genome_obj, set([""]))







def retrieve_phagesdb_data(phage_url):
    """Retrieve all data from PhagesDB for a specific phage."""

    try:
        data_json = urllib.request.urlopen(phage_url)
        data_dict = json.loads(data_json.read())
    except:
        data_dict = {}
    return data_dict

def construct_phage_url(phage_name):
    """Create URL to retrieve phage-specific data from PhagesDB."""
    phage_url = constants.API_PREFIX + phage_name + constants.API_SUFFIX
    return phage_url


def copy_data_from_phagesdb(bundle, type, flag = "retrieve"):
    """If a genome object stored in the Bundle object has
    attributes that are set to be 'retrieved' and auto-filled,
    retrieve the data from PhagesDB to complete the genome.
    The 'type' parameter indicates the type of genome that may need
    to be populated from PhagesDB."""

    if type in bundle.genome_dict.keys():

        genome1 = bundle.genome_dict[type]
        genome1.set_empty_fields(flag)

        if genome1._empty_fields:

            phage_url = construct_phage_url(genome1.id)
            data_dict = retrieve_phagesdb_data(phage_url)

            # If there was an error with retrieving data from PhagesDB,
            # an empty dictionary is returned.
            if len(data_dict.keys()) != 0:

                genome2 = Genome.Genome()
                parse_phagesdb_data(genome2, data_dict)
                bundle.genome_dict[genome2.type] = genome2


                # Copy all retrieved data and add to Bundle object.
                genome_pair = GenomePair.GenomePair()
                genome_pair.genome1 = genome1
                genome_pair.genome2 = genome2
                genome_pair.copy_data("type", genome2.type, genome1.type, flag)
                bundle.set_genome_pair(genome_pair, genome1.type, genome2.type)


        # Now record an error if there are still fields
        # that need to be retrieved.
        genome1.set_empty_fields(flag)
        genome1.check_empty_fields()


def retrieve_phagesdb_data_list(url):
    """Retrieve list of data from PhagesDB."""

    try:
        data_json = urllib.request.urlopen(url)
        data_list = json.loads(data_json.read())
    except:
        data_list = []
    return data_list


def create_host_genus_set(url = constants.API_HOST_GENERA):
    """Create a set of host genera currently in PhagesDB.
    The parameter is a list, and each element is a dictionary of data
    pertaining to a different host genus."""

    try:
        output = retrieve_phagesdb_data_list(url)
    except:
        output = []

    host_genera_set = set()
    for genus_dict in output:
        try:
            host_genera_set.add(genus_dict["genus_name"])
        except:
            pass
    return host_genera_set


def create_cluster_subcluster_sets(url = constants.API_CLUSTERS):
    """Create sets of clusters and subclusters currently in PhagesDB.
    The parameter is a list, and each element is a dictionary of data
    pertaining to a different cluster."""

    try:
        output = retrieve_phagesdb_data_list(url)
    except:
        output = []

    cluster_set = set()
    subcluster_set = set()
    for data in output:
        try:
            # This set will contain "Singleton".
            cluster_set.add(data["cluster"])
            try:
                subclusters_list = data["subclusters_set"]
                subcluster_set = subcluster_set | set(subclusters_list)
            except:
                pass
        except:
            pass

    return (cluster_set, subcluster_set)

















###
