""" Unit tests for import functions."""

from datetime import datetime
from pdm_utils.classes import bundle
from pdm_utils.classes import genome
from pdm_utils.classes import source
from pdm_utils.classes import cds
from pdm_utils.classes import genomepair
from pdm_utils.constants import constants
from pdm_utils.functions import run_modes
from pdm_utils.pipelines.db_import import import_genome
from pdm_utils.classes import ticket, eval
import unittest
from Bio.Seq import Seq
from unittest.mock import patch
from pdm_utils.classes import mysqlconnectionhandler as mch
from Bio.Alphabet import IUPAC

def get_errors(item):
    errors = 0
    for evl in item.evaluations:
        if evl.status == "error":
            errors += 1
    return errors


class TestImportGenomeClass1(unittest.TestCase):


    def setUp(self):

        self.null_set = constants.EMPTY_SET
        self.type_set = constants.IMPORT_TICKET_TYPE_SET
        self.run_mode_set = run_modes.RUN_MODES.keys()
        self.description_field_set = constants.DESCRIPTION_FIELD_SET

        self.retain_set = constants.IMPORT_TABLE_VALID_RETAIN_FIELDS
        self.retrieve_set = constants.IMPORT_TABLE_VALID_RETRIEVE_FIELDS
        self.ticket_set = self.retain_set | self.retrieve_set


        self.data_dict = {
            "host_genus": "Mycobacterium smegmatis",
            "cluster": "A",
            "subcluster": "A2",
            "annotation_status": "draft",
            "annotation_author": 1,
            "retrieve_record": 1,
            "accession": "ABC123.1"
            }

        self.tkt = ticket.GenomeTicket()
        self.tkt.id = 1
        self.tkt.type = "replace"
        self.tkt.phage_id = "Trixie"
        self.tkt.run_mode = "phagesdb"
        self.tkt.description_field = "product"
        self.tkt.data_dict = self.data_dict
        self.tkt.eval_flags = {"a":1, "b":2}
        self.tkt.data_retain = set(["host_genus"])
        self.tkt.data_retrieve = set(["cluster"])
        self.tkt.data_ticket = set(["retrieve_record"])


    def test_check_ticket_1(self):
        """Verify no error is produced with a correctly structured
        'replace' ticket."""
        import_genome.check_ticket(
            self.tkt, type_set=self.type_set,
            description_field_set=self.description_field_set,
            null_set=self.null_set, run_mode_set=self.run_mode_set,
            id_dupe_set=set(), phage_id_dupe_set=set(),
            retain_set=self.retain_set, retrieve_set=self.retrieve_set,
            ticket_set=self.ticket_set)
        errors = get_errors(self.tkt)
        with self.subTest():
            self.assertEqual(len(self.tkt.evaluations), 11)
        with self.subTest():
            self.assertEqual(errors, 0)

    def test_check_ticket_2(self):
        """Verify correct number of errors is produced with
        a duplicate id."""
        import_genome.check_ticket(
            self.tkt, type_set=self.type_set,
            description_field_set=self.description_field_set,
            null_set=self.null_set, run_mode_set=self.run_mode_set,
            id_dupe_set=set([1]), phage_id_dupe_set=set(),
            retain_set=self.retain_set, retrieve_set=self.retrieve_set,
            ticket_set=self.ticket_set)
        errors = get_errors(self.tkt)
        self.assertEqual(errors, 1)

    def test_check_ticket_3(self):
        """Verify correct number of errors is produced with
        a duplicate phage_id."""
        import_genome.check_ticket(
            self.tkt, type_set=self.type_set,
            description_field_set=self.description_field_set,
            null_set=self.null_set, run_mode_set=self.run_mode_set,
            id_dupe_set=set(), phage_id_dupe_set=set(["Trixie"]),
            retain_set=self.retain_set, retrieve_set=self.retrieve_set,
            ticket_set=self.ticket_set)
        errors = get_errors(self.tkt)
        self.assertEqual(errors, 1)

    def test_check_ticket_4(self):
        """Verify correct number of errors is produced with
        an invalid type."""
        self.tkt.type = "invalid"
        import_genome.check_ticket(
            self.tkt, type_set=self.type_set,
            description_field_set=self.description_field_set,
            null_set=self.null_set, run_mode_set=self.run_mode_set,
            id_dupe_set=set(), phage_id_dupe_set=set(),
            retain_set=self.retain_set, retrieve_set=self.retrieve_set,
            ticket_set=self.ticket_set)
        errors = get_errors(self.tkt)
        self.assertEqual(errors, 1)

    def test_check_ticket_5(self):
        """Verify correct number of errors is produced with
        an invalid description_field."""
        self.tkt.description_field = "invalid"
        import_genome.check_ticket(
            self.tkt, type_set=self.type_set,
            description_field_set=self.description_field_set,
            null_set=self.null_set, run_mode_set=self.run_mode_set,
            id_dupe_set=set(), phage_id_dupe_set=set(),
            retain_set=self.retain_set, retrieve_set=self.retrieve_set,
            ticket_set=self.ticket_set)
        errors = get_errors(self.tkt)
        self.assertEqual(errors, 1)

    def test_check_ticket_6(self):
        """Verify correct number of errors is produced with
        an invalid run_mode."""
        self.tkt.run_mode = "invalid"
        import_genome.check_ticket(
            self.tkt, type_set=self.type_set,
            description_field_set=self.description_field_set,
            null_set=self.null_set, run_mode_set=self.run_mode_set,
            id_dupe_set=set(), phage_id_dupe_set=set(),
            retain_set=self.retain_set, retrieve_set=self.retrieve_set,
            ticket_set=self.ticket_set)
        errors = get_errors(self.tkt)
        self.assertEqual(errors, 1)

    def test_check_ticket_7(self):
        """Verify correct number of errors is produced with
        an invalid eval_flag dictionary."""
        self.tkt.eval_flags = {}
        import_genome.check_ticket(
            self.tkt, type_set=self.type_set,
            description_field_set=self.description_field_set,
            null_set=self.null_set, run_mode_set=self.run_mode_set,
            id_dupe_set=set(), phage_id_dupe_set=set(),
            retain_set=self.retain_set, retrieve_set=self.retrieve_set,
            ticket_set=self.ticket_set)
        errors = get_errors(self.tkt)
        self.assertEqual(errors, 1)

    def test_check_ticket_8(self):
        """Verify correct number of errors is produced with
        an invalid phage_id."""
        self.tkt.phage_id = ""
        import_genome.check_ticket(
            self.tkt, type_set=self.type_set,
            description_field_set=self.description_field_set,
            null_set=self.null_set, run_mode_set=self.run_mode_set,
            id_dupe_set=set(), phage_id_dupe_set=set(),
            retain_set=self.retain_set, retrieve_set=self.retrieve_set,
            ticket_set=self.ticket_set)
        errors = get_errors(self.tkt)
        self.assertEqual(errors, 1)

    def test_check_ticket_9(self):
        """Verify correct number of errors is produced with
        an incompatible "add" type and data_retain."""
        self.tkt.type = "add"
        import_genome.check_ticket(
            self.tkt, type_set=self.type_set,
            description_field_set=self.description_field_set,
            null_set=self.null_set, run_mode_set=self.run_mode_set,
            id_dupe_set=set(), phage_id_dupe_set=set(),
            retain_set=self.retain_set, retrieve_set=self.retrieve_set,
            ticket_set=self.ticket_set)
        errors = get_errors(self.tkt)
        self.assertEqual(errors, 1)

    def test_check_ticket_10(self):
        """Verify correct number of errors is produced with
        an data in data_retain."""
        self.tkt.data_retain = set(["invalid"])
        import_genome.check_ticket(
            self.tkt, type_set=self.type_set,
            description_field_set=self.description_field_set,
            null_set=self.null_set, run_mode_set=self.run_mode_set,
            id_dupe_set=set(), phage_id_dupe_set=set(),
            retain_set=self.retain_set, retrieve_set=self.retrieve_set,
            ticket_set=self.ticket_set)
        errors = get_errors(self.tkt)
        self.assertEqual(errors, 1)

    def test_check_ticket_11(self):
        """Verify correct number of errors is produced with
        an data in data_retrieve."""
        self.tkt.data_retrieve = set(["invalid"])
        import_genome.check_ticket(
            self.tkt, type_set=self.type_set,
            description_field_set=self.description_field_set,
            null_set=self.null_set, run_mode_set=self.run_mode_set,
            id_dupe_set=set(), phage_id_dupe_set=set(),
            retain_set=self.retain_set, retrieve_set=self.retrieve_set,
            ticket_set=self.ticket_set)
        errors = get_errors(self.tkt)
        self.assertEqual(errors, 1)

    def test_check_ticket_12(self):
        """Verify correct number of errors is produced with
        an data in data_ticket."""
        self.tkt.data_ticket = set(["invalid"])
        import_genome.check_ticket(
            self.tkt, type_set=self.type_set,
            description_field_set=self.description_field_set,
            null_set=self.null_set, run_mode_set=self.run_mode_set,
            id_dupe_set=set(), phage_id_dupe_set=set(),
            retain_set=self.retain_set, retrieve_set=self.retrieve_set,
            ticket_set=self.ticket_set)
        errors = get_errors(self.tkt)
        self.assertEqual(errors, 1)






class TestImportGenomeClass2(unittest.TestCase):


    def setUp(self):

        self.tkt = ticket.GenomeTicket()
        self.tkt.type = "add"
        self.tkt.eval_flags["check_seq"] = True
        self.tkt.eval_flags["check_id_typo"] = True
        self.tkt.eval_flags["check_host_typo"] = True
        self.tkt.eval_flags["check_author"] = True
        self.tkt.eval_flags["check_trna"] = True
        self.tkt.eval_flags["check_gene"] = True
        self.tkt.eval_flags["check_locus_tag"] = True
        self.tkt.eval_flags["check_description"] = True
        self.tkt.eval_flags["check_description_field"] = True

        self.cds1 = cds.Cds()
        self.cds2 = cds.Cds()
        self.source1 = source.Source()

        self.gnm = genome.Genome()
        self.gnm.id = "Trixie"
        self.gnm.name = "Trixie_Draft"
        self.gnm.host_genus = "Mycobacterium"
        self.gnm.cluster = "A"
        self.gnm.subcluster = "A2"
        self.gnm.accession = "ABC123"
        self.gnm.filename = "Trixie.gb"
        self.gnm.seq = "ATCG"
        self.gnm.annotation_status = "final"
        self.gnm.annotation_author = 1
        self.gnm.retrieve_record = 1
        self.gnm.cds_features = [self.cds1, self.cds2]
        self.gnm.source_features = [self.source1]

        self.null_set = set([""])
        self.id_set = set(["Trixie"])
        self.seq_set = set(["AATTAA"])
        self.host_set = set(["Mycobacterium"])
        self.cluster_set = set(["A", "B"])
        self.subcluster_set = set(["A1, A2"])










class TestImportGenomeClass30(unittest.TestCase):

    def setUp(self):

        self.date_jan1 = datetime.strptime('1/1/2000', '%m/%d/%Y')
        self.date_feb1 = datetime.strptime('2/1/2000', '%m/%d/%Y')
        self.date_feb1_b = datetime.strptime('2/1/2000', '%m/%d/%Y')

        self.gnm1 = genome.Genome()
        self.gnm1.type = "phamerator"
        self.gnm1.id = "Trixie"
        self.gnm1.name = "Trixie_Draft"
        self.gnm1.date = self.date_jan1
        self.gnm1.annotation_status = "draft"
        self.gnm1.seq = Seq("AAAA", IUPAC.ambiguous_dna)
        self.gnm1.length = 4
        self.gnm1.cluster = "A"
        self.gnm1.subcluster = "A2"
        self.gnm1.accession = "ABC123"
        self.gnm1.host_genus = "Mycobacterium"
        self.gnm1.annotation_author = 1
        self.gnm1.retrieve_record = 1
        self.gnm1.translation_table = 11

        self.gnm2 = genome.Genome()
        self.gnm2.type = "flat_file"
        self.gnm2.id = "Trixie"
        self.gnm2.name = "Trixie"
        self.gnm2.date = self.date_feb1
        self.gnm2.annotation_status = "final"
        self.gnm2.seq = Seq("AAAA", IUPAC.ambiguous_dna)
        self.gnm2.length = 4
        self.gnm2.cluster = "A"
        self.gnm2.subcluster = "A2"
        self.gnm2.accession = "ABC123"
        self.gnm2.host_genus = "Mycobacterium"
        self.gnm2.annotation_author = 1
        self.gnm2.retrieve_record = 1
        self.gnm2.translation_table = 11

        self.genome_pair = genomepair.GenomePair()
        self.genome_pair.genome1 = self.gnm1
        self.genome_pair.genome2 = self.gnm2

        self.eval_flags = {"check_replace": True}


    def test_compare_genomes_1(self):
        """Verify correct number of evaluations are produced and
        the correct number of errors when:
        'check_replace' is True, annotation_status = 'draft'."""
        import_genome.compare_genomes(self.genome_pair, self.eval_flags)
        errors = get_errors(self.genome_pair)
        with self.subTest():
            self.assertEqual(len(self.genome_pair.evaluations), 13)
        with self.subTest():
            self.assertEqual(errors, 0)

    def test_compare_genomes_2(self):
        """Verify correct number of evaluations are produced and
        the correct number of errors when:
        'check_replace' is True, annotation_status = 'final'."""
        self.gnm1.annotation_status = "final"
        self.gnm1.name = "Trixie"
        import_genome.compare_genomes(self.genome_pair, self.eval_flags)
        errors = get_errors(self.genome_pair)
        with self.subTest():
            self.assertEqual(len(self.genome_pair.evaluations), 13)
        with self.subTest():
            self.assertEqual(errors, 0)

    def test_compare_genomes_3(self):
        """Verify correct number of evaluations are produced and
        the correct number of errors when:
        'check_replace' is False."""
        self.eval_flags = {"check_replace": False}
        import_genome.compare_genomes(self.genome_pair, self.eval_flags)
        errors = get_errors(self.genome_pair)
        with self.subTest():
            self.assertEqual(len(self.genome_pair.evaluations), 10)
        with self.subTest():
            self.assertEqual(errors, 0)

    def test_compare_genomes_4(self):
        """Verify the correct number of errors when:
        'check_replace' is True, annotation_status = 'draft',
        and 'id' values are different."""
        self.gnm1.id = "L5"
        import_genome.compare_genomes(self.genome_pair, self.eval_flags)
        errors = get_errors(self.genome_pair)
        self.assertEqual(errors, 1)

    def test_compare_genomes_5(self):
        """Verify the correct number of errors when:
        'check_replace' is True, annotation_status = 'draft',
        and 'seq' values are different."""
        self.gnm1.seq = Seq("AAAT", IUPAC.ambiguous_dna)
        import_genome.compare_genomes(self.genome_pair, self.eval_flags)
        errors = get_errors(self.genome_pair)
        self.assertEqual(errors, 1)

    def test_compare_genomes_6(self):
        """Verify the correct number of errors when:
        'check_replace' is True, annotation_status = 'draft',
        and 'length' values are different."""
        self.gnm1.length = 5
        import_genome.compare_genomes(self.genome_pair, self.eval_flags)
        errors = get_errors(self.genome_pair)
        self.assertEqual(errors, 1)

    def test_compare_genomes_7(self):
        """Verify the correct number of errors when:
        'check_replace' is True, annotation_status = 'draft',
        and 'cluster' values are different."""
        self.gnm1.cluster = "B"
        import_genome.compare_genomes(self.genome_pair, self.eval_flags)
        errors = get_errors(self.genome_pair)
        self.assertEqual(errors, 1)

    def test_compare_genomes_8(self):
        """Verify the correct number of errors when:
        'check_replace' is True, annotation_status = 'draft',
        and 'subcluster' values are different."""
        self.gnm1.subcluster = "B2"
        import_genome.compare_genomes(self.genome_pair, self.eval_flags)
        errors = get_errors(self.genome_pair)
        self.assertEqual(errors, 1)

    def test_compare_genomes_9(self):
        """Verify the correct number of errors when:
        'check_replace' is True, annotation_status = 'draft',
        and 'accession' values are different."""
        self.gnm1.accession = "XYZ456"
        import_genome.compare_genomes(self.genome_pair, self.eval_flags)
        errors = get_errors(self.genome_pair)
        self.assertEqual(errors, 1)

    def test_compare_genomes_10(self):
        """Verify the correct number of errors when:
        'check_replace' is True, annotation_status = 'draft',
        and 'host_genus' values are different."""
        self.gnm1.host_genus = "Gordonia"
        import_genome.compare_genomes(self.genome_pair, self.eval_flags)
        errors = get_errors(self.genome_pair)
        self.assertEqual(errors, 1)

    def test_compare_genomes_11(self):
        """Verify the correct number of errors when:
        'check_replace' is True, annotation_status = 'draft',
        and 'annotation_author' values are different."""
        self.gnm1.annotation_author = 0
        import_genome.compare_genomes(self.genome_pair, self.eval_flags)
        errors = get_errors(self.genome_pair)
        self.assertEqual(errors, 1)

    def test_compare_genomes_12(self):
        """Verify the correct number of errors when:
        'check_replace' is True, annotation_status = 'draft',
        and 'translation_table' values are different."""
        self.gnm1.translation_table = 1
        import_genome.compare_genomes(self.genome_pair, self.eval_flags)
        errors = get_errors(self.genome_pair)
        self.assertEqual(errors, 1)

    def test_compare_genomes_13(self):
        """Verify the correct number of errors when:
        'check_replace' is True, annotation_status = 'draft',
        and 'retrieve_record' values are different."""
        self.gnm1.retrieve_record = 0
        import_genome.compare_genomes(self.genome_pair, self.eval_flags)
        errors = get_errors(self.genome_pair)
        self.assertEqual(errors, 1)

    def test_compare_genomes_14(self):
        """Verify the correct number of errors when:
        'check_replace' is True, annotation_status = 'draft',
        and 'date' values are not expected."""
        self.gnm1.date = self.date_feb1
        self.gnm2.date = self.date_jan1
        import_genome.compare_genomes(self.genome_pair, self.eval_flags)
        errors = get_errors(self.genome_pair)
        self.assertEqual(errors, 1)

    def test_compare_genomes_15(self):
        """Verify the correct number of errors when:
        'check_replace' is True, annotation_status = 'draft',
        and 'annotation_status' values are the same."""
        self.gnm2.annotation_status = "draft"
        import_genome.compare_genomes(self.genome_pair, self.eval_flags)
        errors = get_errors(self.genome_pair)
        self.assertEqual(errors, 1)

    def test_compare_genomes_16(self):
        """Verify the correct number of errors when:
        'check_replace' is True, annotation_status = 'draft',
        and 'name' values are the same."""
        self.gnm2.name = "Trixie_Draft"
        import_genome.compare_genomes(self.genome_pair, self.eval_flags)
        errors = get_errors(self.genome_pair)
        self.assertEqual(errors, 1)

    def test_compare_genomes_17(self):
        """Verify the correct number of errors when:
        'check_replace' is True, annotation_status = 'final',
        and 'annotation_status' values are not the same."""
        self.gnm1.annotation_status = "final"
        self.gnm1.name = "Trixie"
        self.gnm2.annotation_status = "unknown"
        import_genome.compare_genomes(self.genome_pair, self.eval_flags)
        errors = get_errors(self.genome_pair)
        self.assertEqual(errors, 1)

    def test_compare_genomes_18(self):
        """Verify the correct number of errors when:
        'check_replace' is True, annotation_status = 'final',
        and 'name' values are not the same."""
        self.gnm1.annotation_status = "final"
        import_genome.compare_genomes(self.genome_pair, self.eval_flags)
        errors = get_errors(self.genome_pair)
        self.assertEqual(errors, 1)





    # TODO fix these tests after fixing check_ticket()
    # def test_check_genome_1(self):
    #     """Verify correct number of evaluations are produced using
    #     'add' ticket and all eval_flags 'True'."""
    #     import_genome.check_genome(self.gnm, self.tkt.type,
    #         self.tkt.eval_flags, self.null_set,
    #         self.id_set, self.seq_set, self.host_set,
    #         self.cluster_set, self.subcluster_set)
    #     self.assertEqual(len(self.gnm.evaluations), 29)
    #
    # def test_check_genome_2(self):
    #     """Verify correct number of evaluations are produced using
    #     'replace' ticket."""
    #     self.tkt.type = "replace"
    #     import_genome.check_genome(self.gnm, self.tkt.type,
    #         self.tkt.eval_flags, self.null_set,
    #         self.id_set, self.seq_set, self.host_set,
    #         self.cluster_set, self.subcluster_set)
    #     self.assertEqual(len(self.gnm.evaluations), 28)
    #
    # def test_check_genome_3(self):
    #     """Verify correct number of evaluations are produced using
    #     'check_seq' as False."""
    #     self.tkt.eval_flags["check_seq"] = False
    #     import_genome.check_genome(self.gnm, self.tkt.type,
    #         self.tkt.eval_flags, self.null_set,
    #         self.id_set, self.seq_set, self.host_set,
    #         self.cluster_set, self.subcluster_set)
    #     self.assertEqual(len(self.gnm.evaluations), 28)
    #
    # def test_check_genome_4(self):
    #     """Verify correct number of evaluations are produced using
    #     'check_id_typo' as False."""
    #     self.tkt.eval_flags["check_id_typo"] = False
    #     import_genome.check_genome(self.gnm, self.tkt.type,
    #         self.tkt.eval_flags, self.null_set,
    #         self.id_set, self.seq_set, self.host_set,
    #         self.cluster_set, self.subcluster_set)
    #     self.assertEqual(len(self.gnm.evaluations), 26)
    #
    # def test_check_genome_5(self):
    #     """Verify correct number of evaluations are produced using
    #     'check_host_typo' as False."""
    #     self.tkt.eval_flags["check_host_typo"] = False
    #     import_genome.check_genome(self.gnm, self.tkt.type,
    #         self.tkt.eval_flags, self.null_set,
    #         self.id_set, self.seq_set, self.host_set,
    #         self.cluster_set, self.subcluster_set)
    #     self.assertEqual(len(self.gnm.evaluations), 25)
    #
    # def test_check_genome_6(self):
    #     """Verify correct number of evaluations are produced using
    #     'check_author' as False."""
    #     self.tkt.eval_flags["check_author"] = False
    #     import_genome.check_genome(self.gnm, self.tkt.type,
    #         self.tkt.eval_flags, self.null_set,
    #         self.id_set, self.seq_set, self.host_set,
    #         self.cluster_set, self.subcluster_set)
    #     self.assertEqual(len(self.gnm.evaluations), 27)




class TestImportGenomeClass3(unittest.TestCase):

    def setUp(self):
        self.tkt = ticket.GenomeTicket()

        self.tkt.type = "replace"
        self.tkt.data_retrieve = set(["cluster"])
        self.tkt.data_retain = set(["subcluster"])
        self.tkt.data_ticket = set(["host_genus"])

        self.gnm1 = genome.Genome()
        self.gnm2 = genome.Genome()
        self.gnm2.annotation_status = "final"
        self.gnm3 = genome.Genome()
        self.gnm4 = genome.Genome()

        self.genome_pair = genomepair.GenomePair()

        self.bndl = bundle.Bundle()
        self.bndl.ticket = self.tkt
        self.bndl.genome_dict["ticket"] = self.gnm1
        self.bndl.genome_dict["flat_file"] = self.gnm2
        self.bndl.genome_dict["phagesdb"] = self.gnm3
        self.bndl.genome_dict["phamerator"] = self.gnm4
        self.bndl.set_genome_pair(self.genome_pair, "flat_file", "phamerator")




    def test_check_bundle_1(self):
        """Verify all check methods are called with no errors."""
        import_genome.check_bundle(self.bndl,
                                   tkt_key="ticket",
                                   file_key="flat_file",
                                   retrieve_key="phagesdb",
                                   retain_key="phamerator")
        errors = get_errors(self.bndl)
        with self.subTest():
            self.assertEqual(len(self.bndl.evaluations), 7)
        with self.subTest():
            self.assertEqual(errors, 0)

    def test_check_bundle_2(self):
        """Verify correct number of errors and check methods called
        with no ticket."""
        self.bndl.ticket = None
        import_genome.check_bundle(self.bndl,
                                   tkt_key="ticket",
                                   file_key="flat_file",
                                   retrieve_key="phagesdb",
                                   retain_key="phamerator")
        errors = get_errors(self.bndl)
        with self.subTest():
            self.assertEqual(len(self.bndl.evaluations), 1)
        with self.subTest():
            self.assertEqual(errors, 1)

    def test_check_bundle_3(self):
        """Verify correct number of errors and check methods called
        with incorrect flat_file key."""
        import_genome.check_bundle(self.bndl,
                                   tkt_key="ticket",
                                   file_key="flat_file_x",
                                   retrieve_key="phagesdb",
                                   retain_key="phamerator")
        errors = get_errors(self.bndl)
        with self.subTest():
            self.assertEqual(len(self.bndl.evaluations), 6)
        with self.subTest():
            self.assertEqual(errors, 2)

    def test_check_bundle_4(self):
        """Verify correct number of errors and check methods called
        with incompatible "replace" ticket type and "draft" annotation status."""
        self.gnm2.annotation_status = "draft"
        import_genome.check_bundle(self.bndl,
                                   tkt_key="ticket",
                                   file_key="flat_file",
                                   retrieve_key="phagesdb",
                                   retain_key="phamerator")
        errors = get_errors(self.bndl)
        with self.subTest():
            self.assertEqual(len(self.bndl.evaluations), 7)
        with self.subTest():
            self.assertEqual(errors, 1)

    def test_check_bundle_5(self):
        """Verify correct number of errors and check methods called
        with no data in data_ticket."""
        self.tkt.data_ticket = set()
        import_genome.check_bundle(self.bndl,
                                   tkt_key="ticket",
                                   file_key="flat_file",
                                   retrieve_key="phagesdb",
                                   retain_key="phamerator")
        errors = get_errors(self.bndl)
        with self.subTest():
            self.assertEqual(len(self.bndl.evaluations), 6)
        with self.subTest():
            self.assertEqual(errors, 0)

    def test_check_bundle_6(self):
        """Verify correct number of errors and check methods called
        with incorrect ticket key."""
        import_genome.check_bundle(self.bndl,
                                   tkt_key="ticket_x",
                                   file_key="flat_file",
                                   retrieve_key="phagesdb",
                                   retain_key="phamerator")
        errors = get_errors(self.bndl)
        with self.subTest():
            self.assertEqual(len(self.bndl.evaluations), 7)
        with self.subTest():
            self.assertEqual(errors, 1)

    def test_check_bundle_7(self):
        """Verify correct number of errors and check methods called
        with no data in data_retrieve."""
        self.tkt.data_retrieve = set()
        import_genome.check_bundle(self.bndl,
                                   tkt_key="ticket",
                                   file_key="flat_file",
                                   retrieve_key="phagesdb",
                                   retain_key="phamerator")
        errors = get_errors(self.bndl)
        with self.subTest():
            self.assertEqual(len(self.bndl.evaluations), 6)
        with self.subTest():
            self.assertEqual(errors, 0)

    def test_check_bundle_8(self):
        """Verify correct number of errors and check methods called
        with incorrect retrieve key."""
        import_genome.check_bundle(self.bndl,
                                   tkt_key="ticket",
                                   file_key="flat_file",
                                   retrieve_key="phagesdb_x",
                                   retain_key="phamerator")
        errors = get_errors(self.bndl)
        with self.subTest():
            self.assertEqual(len(self.bndl.evaluations), 7)
        with self.subTest():
            self.assertEqual(errors, 1)

    def test_check_bundle_9(self):
        """Verify correct number of errors and check methods called
        with "add" ticket type and "draft" annotation status."""
        self.tkt.type = "add"
        self.gnm2.annotation_status = "draft"
        import_genome.check_bundle(self.bndl,
                                   tkt_key="ticket",
                                   file_key="flat_file",
                                   retrieve_key="phagesdb",
                                   retain_key="phamerator")
        errors = get_errors(self.bndl)
        with self.subTest():
            self.assertEqual(len(self.bndl.evaluations), 5)
        with self.subTest():
            self.assertEqual(errors, 0)

    def test_check_bundle_10(self):
        """Verify correct number of errors and check methods called
        with incorrect retain key."""
        import_genome.check_bundle(self.bndl,
                                   tkt_key="ticket",
                                   file_key="flat_file",
                                   retrieve_key="phagesdb",
                                   retain_key="phamerator_x")
        errors = get_errors(self.bndl)
        with self.subTest():
            self.assertEqual(len(self.bndl.evaluations), 7)
        with self.subTest():
            self.assertEqual(errors, 2)




class TestImportGenomeClass4(unittest.TestCase):

    def setUp(self):
        self.eval_dict = {"check_replace": True,
                         "import_locus_tag": True,
                         "check_locus_tag": True,
                         "check_description_field": True,
                         "check_description": True,
                         "check_trna": True,
                         "check_id_typo": True,
                         "check_host_typo": True,
                         "check_author": True,
                         "check_gene": True,
                         "check_seq": True}

        self.tkt = ticket.GenomeTicket()
        self.tkt.phage_id = "Trixie"
        self.tkt.eval_flags = self.eval_dict
        self.tkt.description_field = "product"

        self.cds1 = cds.Cds()
        self.cds2 = cds.Cds()

        # TODO using a Cds object since tRNA object is not available yet.
        self.trna1 = cds.Cds()
        self.trna2 = cds.Cds()

        self.src1 = source.Source()
        self.src2 = source.Source()

        self.gnm1 = genome.Genome()
        self.gnm1.id = "Trixie"

        self.gnm2 = genome.Genome()
        self.gnm2.type = "phamerator"
        self.gnm2.id = "Trixie"

        self.genome_pair = genomepair.GenomePair()
        self.genome_pair.genome1 = self.gnm1
        self.genome_pair.genome2 = self.gnm2

        self.bndl = bundle.Bundle()

        self.null_set = set(["", "none", None])
        self.accession_set = set(["ABC123", "XYZ456"])
        self.phage_id_set = set(["L5", "Trixie"])
        self.seq_set = set(["AATTGG", "ATGC"])
        self.host_genus_set = set(["Mycobacterium", "Gordonia"])
        self.cluster_set = set(["A", "B"])
        self.subcluster_set = set(["A2", "B2"])

        self.sql_handle = mch.MySQLConnectionHandler()



    # TODO fix these after done with compare_genomes(), since number of
    # parameters has changed.
    # def test_run_checks_1(self):
    #     """Verify run_checks works using a bundle with:
    #     no ticket, no "flat_file" genome."""
    #     import_genome.run_checks(
    #             self.bndl,
    #             null_set=self.null_set,
    #             accession_set=self.accession_set,
    #             phage_id_set=self.phage_id_set,
    #             seq_set=self.seq_set, host_genus_set=self.host_genus_set,
    #             cluster_set=self.cluster_set,
    #             subcluster_set=self.subcluster_set,
    #             gnm_key="flat_file",
    #             gnm_pair_key="flat_file_phamerator")
    #     with self.subTest():
    #         self.assertTrue(len(self.bndl.evaluations) > 0)
    #     with self.subTest():
    #         self.assertTrue(len(self.gnm1.evaluations) == 0)
    #
    #
    # def test_run_checks_2(self):
    #     """Verify run_checks works using a bundle with:
    #     'add' ticket, no "flat_file" genome."""
    #     self.tkt.type = "add"
    #     self.bndl.ticket = self.tkt
    #     import_genome.run_checks(
    #             self.bndl,
    #             null_set=self.null_set,
    #             accession_set=self.accession_set,
    #             phage_id_set=self.phage_id_set,
    #             seq_set=self.seq_set, host_genus_set=self.host_genus_set,
    #             cluster_set=self.cluster_set,
    #             subcluster_set=self.subcluster_set,
    #             gnm_key="flat_file",
    #             gnm_pair_key="flat_file_phamerator")
    #     with self.subTest():
    #         self.assertTrue(len(self.bndl.evaluations) > 0)
    #     with self.subTest():
    #         self.assertTrue(len(self.gnm1.evaluations) == 0)
    #
    #
    # def test_run_checks_3(self):
    #     """Verify run_checks works using a bundle with:
    #     'add' ticket, 'flat_file' genome with no features."""
    #     self.tkt.type = "add"
    #     self.bndl.ticket = self.tkt
    #     self.bndl.genome_dict["flat_file"] = self.gnm1
    #     import_genome.run_checks(
    #             self.bndl,
    #             null_set=self.null_set,
    #             accession_set=self.accession_set,
    #             phage_id_set=self.phage_id_set,
    #             seq_set=self.seq_set, host_genus_set=self.host_genus_set,
    #             cluster_set=self.cluster_set,
    #             subcluster_set=self.subcluster_set,
    #             gnm_key="flat_file",
    #             gnm_pair_key="flat_file_phamerator")
    #     with self.subTest():
    #         self.assertTrue(len(self.bndl.evaluations) > 0)
    #     with self.subTest():
    #         self.assertTrue(len(self.gnm1.evaluations) > 0)
    #     with self.subTest():
    #         self.assertTrue(len(self.cds1.evaluations) == 0)
    #     with self.subTest():
    #         self.assertTrue(len(self.cds2.evaluations) == 0)
    #     with self.subTest():
    #         self.assertTrue(len(self.src1.evaluations) == 0)
    #     with self.subTest():
    #         self.assertTrue(len(self.src2.evaluations) == 0)
    #
    #
    # def test_run_checks_4(self):
    #     """Verify run_checks works using a bundle with:
    #     'add' ticket, 'flat_file' genome with two CDS features,
    #     two Source features, and two tRNA features."""
    #     self.tkt.type = "add"
    #     self.bndl.ticket = self.tkt
    #     self.gnm1.cds_features = [self.cds1, self.cds2]
    #     self.gnm1.source_features = [self.src1, self.src2]
    #     self.gnm1.trna_features = [self.trna1, self.trna2]
    #     self.bndl.genome_dict["flat_file"] = self.gnm1
    #     import_genome.run_checks(
    #             self.bndl,
    #             null_set=self.null_set,
    #             accession_set=self.accession_set,
    #             phage_id_set=self.phage_id_set,
    #             seq_set=self.seq_set, host_genus_set=self.host_genus_set,
    #             cluster_set=self.cluster_set,
    #             subcluster_set=self.subcluster_set,
    #             gnm_key="flat_file",
    #             gnm_pair_key="flat_file_phamerator")
    #     with self.subTest():
    #         self.assertTrue(len(self.bndl.evaluations) > 0)
    #     with self.subTest():
    #         self.assertTrue(len(self.gnm1.evaluations) > 0)
    #     with self.subTest():
    #         self.assertTrue(len(self.cds1.evaluations) > 0)
    #     with self.subTest():
    #         self.assertTrue(len(self.cds2.evaluations) > 0)
    #     with self.subTest():
    #         self.assertTrue(len(self.src1.evaluations) > 0)
    #     with self.subTest():
    #         self.assertTrue(len(self.src2.evaluations) > 0)
    #
    #
    # def test_run_checks_5(self):
    #     """Verify run_checks works using a bundle with:
    #     'add' ticket, no genome, 'flat_file_phamerator' genome_pair."""
    #     self.tkt.type = "add"
    #     self.bndl.ticket = self.tkt
    #     self.bndl.genome_pair_dict["flat_file_phamerator"] = self.genome_pair
    #     import_genome.run_checks(
    #             self.bndl,
    #             null_set=self.null_set,
    #             accession_set=self.accession_set,
    #             phage_id_set=self.phage_id_set,
    #             seq_set=self.seq_set, host_genus_set=self.host_genus_set,
    #             cluster_set=self.cluster_set,
    #             subcluster_set=self.subcluster_set,
    #             gnm_key="flat_file",
    #             gnm_pair_key="flat_file_phamerator")
    #     with self.subTest():
    #         self.assertTrue(len(self.bndl.evaluations) > 0)
    #     with self.subTest():
    #         self.assertTrue(len(self.genome_pair.evaluations) == 0)
    #     with self.subTest():
    #         self.assertTrue(len(self.gnm1.evaluations) == 0)
    #
    #
    # def test_run_checks_6(self):
    #     """Verify run_checks works using a bundle with:
    #     'replace' ticket, no genome, 'flat_file_phamerator' genome_pair."""
    #     self.tkt.type = "replace"
    #     self.bndl.ticket = self.tkt
    #     self.bndl.genome_pair_dict["flat_file_phamerator"] = self.genome_pair
    #     import_genome.run_checks(
    #             self.bndl,
    #             null_set=self.null_set,
    #             accession_set=self.accession_set,
    #             phage_id_set=self.phage_id_set,
    #             seq_set=self.seq_set, host_genus_set=self.host_genus_set,
    #             cluster_set=self.cluster_set,
    #             subcluster_set=self.subcluster_set,
    #             gnm_key="flat_file",
    #             gnm_pair_key="flat_file_phamerator")
    #     with self.subTest():
    #         self.assertTrue(len(self.bndl.evaluations) > 0)
    #     with self.subTest():
    #         self.assertTrue(len(self.genome_pair.evaluations) > 0)
    #     with self.subTest():
    #         self.assertTrue(len(self.gnm1.evaluations) == 0)
    #
    #
    # def test_run_checks_7(self):
    #     """Verify run_checks works using a bundle with:
    #     'replace' ticket, no matching genome, no matching genome_pair."""
    #     self.tkt.type = "replace"
    #     self.bndl.ticket = self.tkt
    #     self.gnm1.cds_features = [self.cds1, self.cds2]
    #     self.gnm1.source_features = [self.src1, self.src2]
    #     self.gnm1.trna_features = [self.trna1, self.trna2]
    #     self.bndl.genome_dict["flat_file_x"] = self.gnm1
    #     self.bndl.genome_pair_dict["flat_file_phamerator_x"] = self.genome_pair
    #     import_genome.run_checks(
    #             self.bndl,
    #             null_set=self.null_set,
    #             accession_set=self.accession_set,
    #             phage_id_set=self.phage_id_set,
    #             seq_set=self.seq_set, host_genus_set=self.host_genus_set,
    #             cluster_set=self.cluster_set,
    #             subcluster_set=self.subcluster_set,
    #             gnm_key="flat_file",
    #             gnm_pair_key="flat_file_phamerator")
    #     with self.subTest():
    #         self.assertTrue(len(self.bndl.evaluations) > 0)
    #     with self.subTest():
    #         self.assertTrue(len(self.genome_pair.evaluations) == 0)
    #     with self.subTest():
    #         self.assertTrue(len(self.gnm1.evaluations) == 0)
    #     with self.subTest():
    #         self.assertTrue(len(self.cds1.evaluations) == 0)
    #     with self.subTest():
    #         self.assertTrue(len(self.cds2.evaluations) == 0)
    #     with self.subTest():
    #         self.assertTrue(len(self.src1.evaluations) == 0)
    #     with self.subTest():
    #         self.assertTrue(len(self.src2.evaluations) == 0)



    def test_import_into_db_1(self):
        """Verify import_into_db works using a bundle with:
        1 error, prod_run = True."""
        self.bndl._errors = 1
        result = import_genome.import_into_db(self.bndl, self.sql_handle,
                    gnm_key="", prod_run=True)
        self.assertFalse(result)


    def test_import_into_db_2(self):
        """Verify import_into_db works using a bundle with:
        0 errors, genome present, prod_run = False."""
        self.bndl._errors = 0
        self.tkt.type = "replace"
        self.bndl.ticket = self.tkt
        self.bndl.genome_dict["flat_file"] = self.gnm1
        result = import_genome.import_into_db(self.bndl, self.sql_handle,
                    gnm_key="flat_file", prod_run=False)
        self.assertTrue(result)





    @patch("pdm_utils.classes.mysqlconnectionhandler.MySQLConnectionHandler.execute_transaction")
    def test_import_into_db_3(self, execute_transaction_mock):
        """Verify import_into_db works using a bundle with:
        0 errors, genome present, prod_run = True, execution = failed."""
        execute_transaction_mock.return_value = 1
        self.bndl._errors = 0
        self.tkt.type = "replace"
        self.bndl.ticket = self.tkt
        self.bndl.genome_dict["flat_file"] = self.gnm1
        result = import_genome.import_into_db(self.bndl, self.sql_handle,
                    gnm_key="flat_file", prod_run=True)
        self.assertFalse(result)

    @patch("pdm_utils.classes.mysqlconnectionhandler.MySQLConnectionHandler.execute_transaction")
    def test_import_into_db_4(self, execute_transaction_mock):
        """Verify import_into_db works using a bundle with:
        0 errors, genome present, prod_run = True, execution = successful."""
        execute_transaction_mock.return_value = 0
        self.bndl._errors = 0
        self.tkt.type = "replace"
        self.bndl.ticket = self.tkt
        self.bndl.genome_dict["flat_file"] = self.gnm1
        result = import_genome.import_into_db(self.bndl, self.sql_handle,
                    gnm_key="flat_file", prod_run=True)
        self.assertTrue(result)





class TestImportGenomeClass5(unittest.TestCase):
    def setUp(self):
        self.evl1 = eval.Eval()
        self.evl1.id = "GNM0001"
        self.evl1.definition = "temp"
        self.evl1.status = "error"
        self.evl1.result = "Failed evaluation."

        self.evl2 = eval.Eval()
        self.evl2.id = "GNM0002"
        self.evl2.definition = "temp"
        self.evl2.status = "error"
        self.evl2.result = "Failed evaluation."

        self.evl3 = eval.Eval()
        self.evl3.id = "GNM0003"
        self.evl3.definition = "temp"
        self.evl3.status = "correct"
        self.evl3.result = "Failed evaluation."


    def test_log_evaluations(self):
        """Verify function executes."""
        evaluation_dict = {1:{"bundle": [self.evl1],
                              "ticket": [self.evl2]},
                           2:{"genome": [self.evl3]}}
        import_genome.log_evaluations(evaluation_dict)











class TestImportGenomeClass6(unittest.TestCase):


    def setUp(self):

        self.cds1 = cds.Cds()
        self.cds1.id = "L5_1"
        self.cds1.name = "1"
        self.cds1.translation = Seq("MF", IUPAC.protein)
        self.cds1.translation_length = 2
        self.cds1.seq = Seq("ATGTTTTGA", IUPAC.unambiguous_dna)
        self.cds1.translation_table = 11
        self.cds1.left = 10
        self.cds1.right = 20
        self.cds1.coordinate_format = "0_half_open"
        self.cds1.strand = "F"
        self.cds1.parts = 1
        self.cds1.length = 9
        self.cds1.genome_id = "L5"
        self.cds1.genome_length = 50000
        self.cds1.pham = 100
        self.cds1.description = "repressor protein"
        self.cds1.processed_description = "repressor"
        self.cds1.locus_tag = "SEA_L5_1"
        self.cds1._locus_tag_num = "1"
        self.cds1.gene = "1"
        self.cds1.product = "repressor protein"
        self.cds1.function = "hypothetical protein"
        self.cds1.note = "protein"
        self.cds1.processed_product = "repressor"
        self.cds1.processed_function = ""
        self.cds1.processed_note = ""
        self.cds1.type = "CDS"

        self.eval_flags = {"check_locus_tag": True,
                           "check_gene": True,
                           "check_description": True,
                           "check_description_field": True}

    def test_check_cds_1(self):
        """Verify correct number of evaluations are produced when
        none are False."""
        import_genome.check_cds(self.cds1, self.eval_flags)
        self.assertEqual(len(self.cds1.evaluations), 12)

    def test_check_cds_2(self):
        """Verify correct number of evaluations are produced when
        check_locus_tag = False."""
        self.eval_flags["check_locus_tag"] = False
        import_genome.check_cds(self.cds1, self.eval_flags)
        self.assertEqual(len(self.cds1.evaluations), 9)

    def test_check_cds_3(self):
        """Verify correct number of evaluations are produced when
        check_gene = False."""
        self.eval_flags["check_gene"] = False
        import_genome.check_cds(self.cds1, self.eval_flags)
        self.assertEqual(len(self.cds1.evaluations), 9)

    def test_check_cds_4(self):
        """Verify correct number of evaluations are produced when
        check_description = False."""
        self.eval_flags["check_description"] = False
        import_genome.check_cds(self.cds1, self.eval_flags)
        self.assertEqual(len(self.cds1.evaluations), 12)

    def test_check_cds_5(self):
        """Verify correct number of evaluations are produced when
        all False."""
        self.eval_flags["check_locus_tag"] = False
        self.eval_flags["check_gene"] = False
        self.eval_flags["check_description"] = False
        self.eval_flags["check_description_field"] = False
        import_genome.check_cds(self.cds1, self.eval_flags)
        self.assertEqual(len(self.cds1.evaluations), 6)

    def test_check_cds_6(self):
        """Verify correct number of errors with correct CDS feature."""
        import_genome.check_cds(self.cds1, self.eval_flags)
        errors = get_errors(self.cds1)
        self.assertEqual(errors, 0)

    def test_check_cds_7(self):
        """Verify correct number of errors with incorrect amino acids."""
        self.cds1.translation = Seq("MB", IUPAC.protein)
        import_genome.check_cds(self.cds1, self.eval_flags)
        errors = get_errors(self.cds1)
        self.assertEqual(errors, 2)

    def test_check_cds_8(self):
        """Verify correct number of errors with incorrect translation."""
        self.cds1.translation = Seq("MM", IUPAC.protein)
        import_genome.check_cds(self.cds1, self.eval_flags)
        errors = get_errors(self.cds1)
        self.assertEqual(errors, 1)

    def test_check_cds_9(self):
        """Verify correct number of errors with missing translation."""
        self.cds1.translation_length = 0
        import_genome.check_cds(self.cds1, self.eval_flags)
        errors = get_errors(self.cds1)
        self.assertEqual(errors, 2)

    def test_check_cds_10(self):
        """Verify correct number of errors with incorrect translation table."""
        self.cds1.translation_table = 1
        import_genome.check_cds(self.cds1, self.eval_flags)
        errors = get_errors(self.cds1)
        self.assertEqual(errors, 1)

    def test_check_cds_11(self):
        """Verify correct number of errors with incorrect left coordinate."""
        self.cds1.left = -1
        import_genome.check_cds(self.cds1, self.eval_flags)
        errors = get_errors(self.cds1)
        self.assertEqual(errors, 1)

    def test_check_cds_12(self):
        """Verify correct number of errors with incorrect strand."""
        self.cds1.strand = "f"
        import_genome.check_cds(self.cds1, self.eval_flags)
        errors = get_errors(self.cds1)
        self.assertEqual(errors, 1)

    def test_check_cds_13(self):
        """Verify correct number of errors with missing locus_tag."""
        self.cds1.locus_tag = ""
        import_genome.check_cds(self.cds1, self.eval_flags)
        errors = get_errors(self.cds1)
        self.assertEqual(errors, 2)

    def test_check_cds_14(self):
        """Verify correct number of errors with incorrect locus_tag."""
        self.cds1.locus_tag = "ABCXYZ"
        import_genome.check_cds(self.cds1, self.eval_flags)
        errors = get_errors(self.cds1)
        self.assertEqual(errors, 1)

    def test_check_cds_15(self):
        """Verify correct number of errors with missing gene qualifier."""
        self.cds1.gene = ""
        import_genome.check_cds(self.cds1, self.eval_flags)
        errors = get_errors(self.cds1)
        self.assertEqual(errors, 3)

    def test_check_cds_16(self):
        """Verify correct number of errors with non-integer gene qualifier."""
        self.cds1.gene = "A"
        import_genome.check_cds(self.cds1, self.eval_flags)
        errors = get_errors(self.cds1)
        self.assertEqual(errors, 2)

    def test_check_cds_17(self):
        """Verify correct number of errors with non-integer gene qualifier."""
        self.cds1.gene = "11"
        import_genome.check_cds(self.cds1, self.eval_flags)
        errors = get_errors(self.cds1)
        self.assertEqual(errors, 1)

    def test_check_cds_18(self):
        """Verify correct number of errors with non-matching integer in
        gene qualifier and locus_tag."""
        self.cds1.gene = "11"
        import_genome.check_cds(self.cds1, self.eval_flags)
        errors = get_errors(self.cds1)
        self.assertEqual(errors, 1)

    def test_check_cds_19(self):
        """Verify correct number of errors with non-matching integer in
        gene qualifier and locus_tag."""
        import_genome.check_cds(self.cds1, self.eval_flags,
                                description_field = "function")
        errors = get_errors(self.cds1)
        self.assertEqual(errors, 1)



class TestImportGenomeClass7(unittest.TestCase):


    def setUp(self):

        self.src1 = source.Source()
        self.src1.id = 1
        self.src1.name = ""
        self.src1.type = "source"
        self.src1.left = 1
        self.src1.right = 50000
        self.src1.organism = "Mycobacterium phage L5"
        self.src1.host = "Mycobacterium smegmatis mc1255"
        self.src1.lab_host = "Mycobacterium smegmatis mc1255"
        self.src1.genome_id = "L5"
        self.src1.genome_host_genus = "Mycobacterium"
        self.src1._organism_name = "L5"
        self.src1._organism_host_genus = "Mycobacterium"
        self.src1._host_host_genus = "Mycobacterium"
        self.src1._lab_host_host_genus = "Mycobacterium"

        self.eval_flags = {"check_id_typo": True,
                           "check_host_typo": True}

    def test_check_source_1(self):
        """Verify correct number of evaluations are produced when
        none are False."""
        import_genome.check_source(self.src1, self.eval_flags)
        self.assertEqual(len(self.src1.evaluations), 4)

    def test_check_source_2(self):
        """Verify correct number of evaluations are produced when
        check_id_typo = False."""
        self.eval_flags["check_id_typo"] = False
        import_genome.check_source(self.src1, self.eval_flags)
        self.assertEqual(len(self.src1.evaluations), 3)

    def test_check_source_3(self):
        """Verify correct number of evaluations are produced when
        check_host_typo = False."""
        self.eval_flags["check_host_typo"] = False
        import_genome.check_source(self.src1, self.eval_flags)
        self.assertEqual(len(self.src1.evaluations), 1)

    def test_check_source_4(self):
        """Verify correct number of evaluations are produced when
        organism is empty."""
        self.src1.organism = ""
        import_genome.check_source(self.src1, self.eval_flags)
        self.assertEqual(len(self.src1.evaluations), 3)

    def test_check_source_5(self):
        """Verify correct number of evaluations are produced when
        host is empty."""
        self.src1.host = ""
        import_genome.check_source(self.src1, self.eval_flags)
        self.assertEqual(len(self.src1.evaluations), 3)

    def test_check_source_6(self):
        """Verify correct number of evaluations are produced when
        lab_host is empty."""
        self.src1.lab_host = ""
        import_genome.check_source(self.src1, self.eval_flags)
        self.assertEqual(len(self.src1.evaluations), 3)

    def test_check_source_7(self):
        """Verify correct number of errors with incorrect organism name."""
        self.src1._organism_name = "Trixie"
        import_genome.check_source(self.src1, self.eval_flags)
        errors = get_errors(self.src1)
        self.assertEqual(errors, 1)

    def test_check_source_8(self):
        """Verify correct number of errors with incorrect organism host genus."""
        self.src1._organism_host_genus = "Gordonia"
        import_genome.check_source(self.src1, self.eval_flags)
        errors = get_errors(self.src1)
        self.assertEqual(errors, 1)

    def test_check_source_9(self):
        """Verify correct number of errors with incorrect host host genus."""
        self.src1._host_host_genus = "Gordonia"
        import_genome.check_source(self.src1, self.eval_flags)
        errors = get_errors(self.src1)
        self.assertEqual(errors, 1)

    def test_check_source_10(self):
        """Verify correct number of errors with incorrect lab host host genus."""
        self.src1._lab_host_host_genus = "Gordonia"
        import_genome.check_source(self.src1, self.eval_flags)
        errors = get_errors(self.src1)
        self.assertEqual(errors, 1)




if __name__ == '__main__':
    unittest.main()
