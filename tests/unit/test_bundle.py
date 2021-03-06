""" Unit tests for the Bundle Class."""

import unittest

from pdm_utils.classes import bundle
from pdm_utils.classes import cds, trna, tmrna, source
from pdm_utils.classes import evaluation
from pdm_utils.classes import genome
from pdm_utils.classes import genomepair
from pdm_utils.classes import ticket


class TestBundleClass1(unittest.TestCase):


    def setUp(self):

        self.bndl = bundle.Bundle()
        self.genome1 = genome.Genome()
        self.genome1.type = "flat_file"
        self.genome2 = genome.Genome()
        self.genome2.type = "mysql"
        self.tkt = ticket.ImportTicket()




    def test_set_genome_pair_1(self):
        """Check that a genome pair is set if both keys are present."""

        self.bndl.ticket = self.tkt
        self.bndl.genome_dict[self.genome1.type] = self.genome1
        self.bndl.genome_dict[self.genome2.type] = self.genome2
        genome_pair = genomepair.GenomePair()
        self.bndl.set_genome_pair(genome_pair, "mysql", "flat_file")
        self.assertEqual(list(self.bndl.genome_pair_dict.keys())[0],
                            "mysql_flat_file")

    def test_set_genome_pair_2(self):
        """Check that a genome pair is not set if one key is not present."""

        self.bndl.ticket = self.tkt
        self.bndl.genome_dict[self.genome1.type] = self.genome1
        self.bndl.genome_dict[self.genome2.type] = self.genome2
        genome_pair = genomepair.GenomePair()
        self.bndl.set_genome_pair(genome_pair, "invalid", "flat_file")
        self.assertEqual(len(self.bndl.genome_pair_dict.keys()), 0)




    def test_check_ticket_1(self):
        """Check that no error is produced when a ticket is present."""
        self.bndl.ticket = self.tkt
        self.bndl.check_ticket("eval_id")
        with self.subTest():
            self.assertEqual(self.bndl.evaluations[0].status, "correct")
        with self.subTest():
            self.assertEqual(self.bndl.evaluations[0].id, "eval_id")

    def test_check_ticket_2(self):
        """Check that an error is produced when a ticket is not present."""
        self.bndl.ticket = None
        self.bndl.check_ticket("eval_id")
        with self.subTest():
            self.assertEqual(self.bndl.evaluations[0].status, "error")
        with self.subTest():
            self.assertEqual(self.bndl.evaluations[0].id, "eval_id")








    def test_check_genome_dict_1(self):
        """Check that no error is produced when a genome is present
        in the dictionary and is expected to be present."""
        self.bndl.genome_dict[self.genome1.type] = self.genome1
        self.bndl.check_genome_dict("flat_file", eval_id="eval_id")
        with self.subTest():
            self.assertEqual(self.bndl.evaluations[0].status, "correct")
        with self.subTest():
            self.assertEqual(self.bndl.evaluations[0].id, "eval_id")

    def test_check_genome_dict_2(self):
        """Check that an error is produced when a genome is not present
        in the dictionary and is expected to be present."""
        self.bndl.genome_dict[self.genome1.type] = self.genome1
        self.bndl.check_genome_dict("flat_file", False)
        with self.subTest():
            self.assertEqual(self.bndl.evaluations[0].status, "error")
        with self.subTest():
            self.assertIsNone(self.bndl.evaluations[0].id)

    def test_check_genome_dict_3(self):
        """Check that no error is produced when a genome is not present
        in the dictionary and is not expected to be present."""
        self.bndl.check_genome_dict("flat_file", False)
        self.assertEqual(self.bndl.evaluations[0].status, "correct")

    def test_check_genome_dict_4(self):
        """Check that an error is produced when a genome is not present
        in the dictionary and is expected to be present."""
        self.bndl.check_genome_dict("flat_file")
        self.assertEqual(self.bndl.evaluations[0].status, "error")




    def test_check_genome_pair_dict_1(self):
        """Check that no error is produced when a genome_pair is present
        in the dictionary and is expected to be present."""
        self.bndl.genome_pair_dict["flat_file_mysql"] = ""
        self.bndl.check_genome_pair_dict(
            "flat_file_mysql", eval_id="eval_id")
        with self.subTest():
            self.assertEqual(self.bndl.evaluations[0].status, "correct")
        with self.subTest():
            self.assertEqual(self.bndl.evaluations[0].id, "eval_id")

    def test_check_genome_pair_dict_2(self):
        """Check that an error is produced when a genome_pair is not present
        in the dictionary and is expected to be present."""
        self.bndl.genome_pair_dict["flat_file_mysql"] = ""
        self.bndl.check_genome_pair_dict("flat_file_mysql", False)
        with self.subTest():
            self.assertEqual(self.bndl.evaluations[0].status, "error")
        with self.subTest():
            self.assertIsNone(self.bndl.evaluations[0].id)

    def test_check_genome_pair_dict_3(self):
        """Check that no error is produced when a genome_pair is not present
        in the dictionary and is not expected to be present."""
        self.bndl.check_genome_pair_dict("flat_file", False)
        self.assertEqual(self.bndl.evaluations[0].status, "correct")

    def test_check_genome_pair_dict_4(self):
        """Check that an error is produced when a genome_pair is not present
        in the dictionary and is expected to be present."""
        self.bndl.check_genome_pair_dict("flat_file")
        self.assertEqual(self.bndl.evaluations[0].status, "error")




    def test_check_statements_1(self):
        """Check that no error is produced when execution of MySQL statements
        is successful."""
        msg = "Successul statement execution."
        self.bndl.check_statements(0, msg, eval_id="eval_id")
        with self.subTest():
            self.assertEqual(self.bndl.evaluations[0].status, "correct")
        with self.subTest():
            self.assertEqual(self.bndl.evaluations[0].id, "eval_id")

    def test_check_statements_2(self):
        """Check that an error is produced when execution of MySQL statements
        is not successful."""
        msg = "Failed statement execution."
        self.bndl.check_statements(1, msg, eval_id="eval_id")
        with self.subTest():
            self.assertEqual(self.bndl.evaluations[0].status, "error")
        with self.subTest():
            self.assertEqual(self.bndl.evaluations[0].id, "eval_id")




class TestBundleClass2(unittest.TestCase):


    def setUp(self):

        self.ticket1 = ticket.ImportTicket()

        self.src1 = source.Source()
        self.src1.id = "L5_SRC_1"
        self.src2 = source.Source()
        self.src2.id = "L5_SRC_2"
        self.src3 = source.Source()
        self.src3.id = "L5_SRC_3"

        self.cds1 = cds.Cds()
        self.cds1.id = "L5_CDS_1"
        self.cds2 = cds.Cds()
        self.cds2.id = "L5_CDS_2"
        self.cds3 = cds.Cds()
        self.cds3.id = "L5_CDS_3"

        self.trna1 = trna.Trna()
        self.trna1.id = "L5_TRNA_1"
        self.trna2 = trna.Trna()
        self.trna2.id = "L5_TRNA_2"
        self.trna3 = trna.Trna()
        self.trna3.id = "L5_TRNA_3"

        self.tmrna1 = tmrna.Tmrna()
        self.tmrna1.id = "L5_TMRNA_1"
        self.tmrna2 = tmrna.Tmrna()
        self.tmrna2.id = "L5_TMRNA_2"
        self.tmrna3 = tmrna.Tmrna()
        self.tmrna3.id = "L5_TMRNA_3"

        self.genome1 = genome.Genome()
        self.genome1.type = "flat_file"
        self.genome1.cds_features = [self.cds1, self.cds2]
        self.genome1.source_features = [self.src1, self.src2]
        self.genome1.trna_features = [self.trna1, self.trna2]
        self.genome1.tmrna_features = [self.tmrna1, self.tmrna2]

        self.genome2 = genome.Genome()
        self.genome2.type = "mysql"
        self.genome_pair1 = genomepair.GenomePair()
        self.genome_pair2 = genomepair.GenomePair()
        self.bndl = bundle.Bundle()
        self.bndl.ticket = self.ticket1
        self.bndl.genome_dict[self.genome1.type] = self.genome1
        self.bndl.genome_dict[self.genome2.type] = self.genome2
        self.bndl.genome_pair_dict["genome_pair1"] = self.genome_pair1
        self.bndl.genome_pair_dict["genome_pair2"] = self.genome_pair2

        self.eval_correct1 = evaluation.Evaluation(status="correct")
        self.eval_correct2 = evaluation.Evaluation(status="correct")
        self.eval_error1 = evaluation.Evaluation(status="error")
        self.eval_error2 = evaluation.Evaluation(status="error")




    def test_check_for_errors_1(self):
        """Check that no error is counted."""
        self.bndl.check_for_errors()
        self.assertEqual(self.bndl._errors, 0)

    def test_check_for_errors_2(self):
        """Check that a Bundle 'correct' evaluation is not counted."""
        self.bndl.evaluations.append(self.eval_correct1)
        self.bndl.check_for_errors()
        self.assertEqual(self.bndl._errors, 0)

    def test_check_for_errors_3(self):
        """Check that a Bundle 'error' evaluation is counted."""
        self.bndl.evaluations.append(self.eval_error1)
        self.bndl.check_for_errors()
        self.assertEqual(self.bndl._errors, 1)

    def test_check_for_errors_4(self):
        """Check that a ticket 'correct' evaluation is not counted."""
        self.ticket1.evaluations.append(self.eval_correct1)
        self.bndl.check_for_errors()
        self.assertEqual(self.bndl._errors, 0)

    def test_check_for_errors_5(self):
        """Check that a ticket 'error' evaluation is counted."""
        self.ticket1.evaluations.append(self.eval_error1)
        self.bndl.check_for_errors()
        self.assertEqual(self.bndl._errors, 1)

    def test_check_for_errors_6(self):
        """Check that a bundle with no ticket is not counted."""
        self.bndl.ticket = None
        self.bndl.check_for_errors()
        self.assertEqual(self.bndl._errors, 0)

    def test_check_for_errors_7(self):
        """Check that a genome 'correct' evaluation is not counted."""
        self.genome1.evaluations.append(self.eval_correct1)
        self.bndl.check_for_errors()
        self.assertEqual(self.bndl._errors, 0)

    def test_check_for_errors_8(self):
        """Check that a genome 'error' evaluation is counted."""
        self.genome1.evaluations.append(self.eval_error1)
        self.bndl.check_for_errors()
        self.assertEqual(self.bndl._errors, 1)

    def test_check_for_errors_9(self):
        """Check that two genome 'correct' evals are not counted."""
        self.genome1.evaluations.append(self.eval_correct1)
        self.genome2.evaluations.append(self.eval_correct2)
        self.bndl.check_for_errors()
        self.assertEqual(self.bndl._errors, 0)

    def test_check_for_errors_10(self):
        """Check that two genome 'error' evals are counted."""
        self.genome1.evaluations.append(self.eval_error1)
        self.genome2.evaluations.append(self.eval_error2)
        self.bndl.check_for_errors()
        self.assertEqual(self.bndl._errors, 2)

    def test_check_for_errors_11(self):
        """Check that a source feature 'correct' evaluation is not counted."""
        self.src1.evaluations.append(self.eval_correct1)
        self.bndl.check_for_errors()
        self.assertEqual(self.bndl._errors, 0)

    def test_check_for_errors_12(self):
        """Check that a source feature 'error' evaluation is counted."""
        self.src1.evaluations.append(self.eval_error1)
        self.bndl.check_for_errors()
        self.assertEqual(self.bndl._errors, 1)

    def test_check_for_errors_13(self):
        """Check that two source feature 'correct' evals are not counted."""
        self.src1.evaluations.append(self.eval_correct1)
        self.src2.evaluations.append(self.eval_correct2)
        self.bndl.check_for_errors()
        self.assertEqual(self.bndl._errors, 0)

    def test_check_for_errors_14(self):
        """Check that two source feature 'error' evals are counted."""
        self.src1.evaluations.append(self.eval_error1)
        self.src2.evaluations.append(self.eval_error2)
        self.bndl.check_for_errors()
        self.assertEqual(self.bndl._errors, 2)

    def test_check_for_errors_15(self):
        """Check that a cds 'correct' evaluation is not counted."""
        self.cds1.evaluations.append(self.eval_correct1)
        self.bndl.check_for_errors()
        self.assertEqual(self.bndl._errors, 0)

    def test_check_for_errors_16(self):
        """Check that a cds 'error' evaluation is counted."""
        self.cds1.evaluations.append(self.eval_error1)
        self.bndl.check_for_errors()
        self.assertEqual(self.bndl._errors, 1)

    def test_check_for_errors_17(self):
        """Check that two cds 'correct' evals are not counted."""
        self.cds1.evaluations.append(self.eval_correct1)
        self.cds2.evaluations.append(self.eval_correct2)
        self.bndl.check_for_errors()
        self.assertEqual(self.bndl._errors, 0)

    def test_check_for_errors_18(self):
        """Check that two cds 'error' evals are counted."""
        self.cds1.evaluations.append(self.eval_error1)
        self.cds2.evaluations.append(self.eval_error2)
        self.bndl.check_for_errors()
        self.assertEqual(self.bndl._errors, 2)

    def test_check_for_errors_19(self):
        """Check that a trna 'correct' evaluation is not counted."""
        self.trna1.evaluations.append(self.eval_correct1)
        self.bndl.check_for_errors()
        self.assertEqual(self.bndl._errors, 0)

    def test_check_for_errors_20(self):
        """Check that a trna 'error' evaluation is counted."""
        self.trna1.evaluations.append(self.eval_error1)
        self.bndl.check_for_errors()
        self.assertEqual(self.bndl._errors, 1)

    def test_check_for_errors_21(self):
        """Check that two trna 'correct' evals are not counted."""
        self.trna1.evaluations.append(self.eval_correct1)
        self.trna2.evaluations.append(self.eval_correct2)
        self.bndl.check_for_errors()
        self.assertEqual(self.bndl._errors, 0)

    def test_check_for_errors_22(self):
        """Check that two trna 'error' evals are counted."""
        self.trna1.evaluations.append(self.eval_error1)
        self.trna2.evaluations.append(self.eval_error2)
        self.bndl.check_for_errors()
        self.assertEqual(self.bndl._errors, 2)

    def test_check_for_errors_23(self):
        """Check that a tmrna 'correct' evaluation is not counted."""
        self.tmrna1.evaluations.append(self.eval_correct1)
        self.bndl.check_for_errors()
        self.assertEqual(self.bndl._errors, 0)

    def test_check_for_errors_24(self):
        """Check that a tmrna 'error' evaluation is counted."""
        self.tmrna1.evaluations.append(self.eval_error1)
        self.bndl.check_for_errors()
        self.assertEqual(self.bndl._errors, 1)

    def test_check_for_errors_25(self):
        """Check that two tmrna 'correct' evals are not counted."""
        self.tmrna1.evaluations.append(self.eval_correct1)
        self.tmrna2.evaluations.append(self.eval_correct2)
        self.bndl.check_for_errors()
        self.assertEqual(self.bndl._errors, 0)

    def test_check_for_errors_26(self):
        """Check that two tmrna 'error' evals are counted."""
        self.tmrna1.evaluations.append(self.eval_error1)
        self.tmrna2.evaluations.append(self.eval_error2)
        self.bndl.check_for_errors()
        self.assertEqual(self.bndl._errors, 2)

    def test_check_for_errors_27(self):
        """Check that a genome_pair 'correct' evaluation is not counted."""
        self.genome_pair1.evaluations.append(self.eval_correct1)
        self.bndl.check_for_errors()
        self.assertEqual(self.bndl._errors, 0)

    def test_check_for_errors_28(self):
        """Check that a genome_pair 'error' evaluation is counted."""
        self.genome_pair1.evaluations.append(self.eval_error1)
        self.bndl.check_for_errors()
        self.assertEqual(self.bndl._errors, 1)

    def test_check_for_errors_29(self):
        """Check that two genome_pair 'correct' evals are not counted."""
        self.genome_pair1.evaluations.append(self.eval_correct1)
        self.genome_pair2.evaluations.append(self.eval_correct2)
        self.bndl.check_for_errors()
        self.assertEqual(self.bndl._errors, 0)

    def test_check_for_errors_30(self):
        """Check that two genome_pair 'error' evals are counted."""
        self.genome_pair1.evaluations.append(self.eval_error1)
        self.genome_pair2.evaluations.append(self.eval_error2)
        self.bndl.check_for_errors()
        self.assertEqual(self.bndl._errors, 2)




    def test_get_evaluations_1(self):
        """Verify one evaluation is returned from Bundle evaluation list."""
        self.bndl.evaluations.append(self.eval_correct1)
        eval_dict = self.bndl.get_evaluations()
        self.assertEqual(len(eval_dict["bundle"]), 1)

    def test_get_evaluations_2(self):
        """Verify one evaluation is returned from Ticket evaluation list."""
        self.ticket1.evaluations.append(self.eval_correct1)
        eval_dict = self.bndl.get_evaluations()
        self.assertEqual(len(eval_dict["ticket"]), 1)

    def test_get_evaluations_3(self):
        """Verify one evaluation is returned from each genome evaluation list."""
        self.genome1.evaluations.append(self.eval_correct1)
        self.genome1.evaluations.append(self.eval_correct2)
        self.genome2.evaluations.append(self.eval_error1)
        eval_dict = self.bndl.get_evaluations()
        with self.subTest():
            self.assertEqual(len(eval_dict["genome_flat_file"]), 2)
        with self.subTest():
            self.assertEqual(len(eval_dict["genome_mysql"]), 1)

    def test_get_evaluations_4(self):
        """Verify one evaluation is returned from each Source evaluation list in
        each genome."""
        self.src1.evaluations.append(self.eval_correct1)
        self.src1.evaluations.append(self.eval_correct2)
        self.src2.evaluations.append(self.eval_error1)
        self.src3.evaluations.append(self.eval_error2)
        self.genome1.source_features = [self.src1, self.src2]
        self.genome2.source_features = [self.src3]
        eval_dict = self.bndl.get_evaluations()
        with self.subTest():
            self.assertEqual(len(eval_dict["src_L5_SRC_1"]), 2)
        with self.subTest():
            self.assertEqual(len(eval_dict["src_L5_SRC_2"]), 1)
        with self.subTest():
            self.assertEqual(len(eval_dict["src_L5_SRC_3"]), 1)

    def test_get_evaluations_5(self):
        """Verify one evaluation is returned from each Cds evaluation list in
        each genome."""
        self.cds1.evaluations.append(self.eval_correct1)
        self.cds1.evaluations.append(self.eval_correct2)
        self.cds2.evaluations.append(self.eval_error1)
        self.cds3.evaluations.append(self.eval_error2)
        self.genome1.cds_features = [self.cds1, self.cds2]
        self.genome2.cds_features = [self.cds3]
        eval_dict = self.bndl.get_evaluations()
        with self.subTest():
            self.assertEqual(len(eval_dict["cds_L5_CDS_1"]), 2)
        with self.subTest():
            self.assertEqual(len(eval_dict["cds_L5_CDS_2"]), 1)
        with self.subTest():
            self.assertEqual(len(eval_dict["cds_L5_CDS_3"]), 1)

    def test_get_evaluations_6(self):
        """Verify one evaluation is returned from each Trna evaluation list in
        each genome."""
        self.trna1.evaluations.append(self.eval_correct1)
        self.trna1.evaluations.append(self.eval_correct2)
        self.trna2.evaluations.append(self.eval_error1)
        self.trna3.evaluations.append(self.eval_error2)
        self.genome1.trna_features = [self.trna1, self.trna2]
        self.genome2.trna_features = [self.trna3]
        eval_dict = self.bndl.get_evaluations()
        with self.subTest():
            self.assertEqual(len(eval_dict["trna_L5_TRNA_1"]), 2)
        with self.subTest():
            self.assertEqual(len(eval_dict["trna_L5_TRNA_2"]), 1)
        with self.subTest():
            self.assertEqual(len(eval_dict["trna_L5_TRNA_3"]), 1)

    def test_get_evaluations_7(self):
        """Verify one evaluation is returned from each Tmrna evaluation list in
        each genome."""
        self.tmrna1.evaluations.append(self.eval_correct1)
        self.tmrna1.evaluations.append(self.eval_correct2)
        self.tmrna2.evaluations.append(self.eval_error1)
        self.tmrna3.evaluations.append(self.eval_error2)
        self.genome1.tmrna_features = [self.tmrna1, self.tmrna2]
        self.genome2.tmrna_features = [self.tmrna3]
        eval_dict = self.bndl.get_evaluations()
        with self.subTest():
            self.assertEqual(len(eval_dict["tmrna_L5_TMRNA_1"]), 2)
        with self.subTest():
            self.assertEqual(len(eval_dict["tmrna_L5_TMRNA_2"]), 1)
        with self.subTest():
            self.assertEqual(len(eval_dict["tmrna_L5_TMRNA_3"]), 1)

    def test_get_evaluations_8(self):
        """Verify one evaluation is returned from each genome_pair
        evaluation list."""
        self.genome_pair1.evaluations.append(self.eval_correct1)
        self.genome_pair1.evaluations.append(self.eval_correct2)
        self.genome_pair2.evaluations.append(self.eval_error1)
        eval_dict = self.bndl.get_evaluations()
        with self.subTest():
            self.assertEqual(len(eval_dict["genome_pair_genome_pair1"]), 2)
        with self.subTest():
            self.assertEqual(len(eval_dict["genome_pair_genome_pair2"]), 1)





if __name__ == '__main__':
    unittest.main()
