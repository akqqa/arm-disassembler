import unittest
from common import *

class TestInstructionMapping(unittest.TestCase):

    # Using the default mapping, extract op0 and op1 from a given instruction string
    def testDefaultExtraction(self):
        mapping = InstructionMapping()
        values = mapping.assignValues("10011110000000000000000000000000")
        self.assertEqual(values[0][0], "op0")
        self.assertEqual(values[1][0], "op1")
        self.assertEqual(values[0][1], "1")
        self.assertEqual(values[1][1], "1111")

    # Test that incorrectly sized instructions return false
    def testShortInstruction(self):
        mapping = InstructionMapping()
        values = mapping.assignValues("1001111000000000000000000000000")
        self.assertEqual(values, False)

    # Tests using a custom mapping
    def testCustomExtraction(self):
        mappings = {
            "test1": [11, 4],
            "test2": [20, 2]
        }
        mapping = InstructionMapping(mappings)
        values = mapping.assignValues("01001101011000101101001010101000")
        self.assertEqual(values[0][0], "test1")
        self.assertEqual(values[1][0], "test2")
        self.assertEqual(values[0][1], "0010")
        self.assertEqual(values[1][1], "00")

class TestCompareWithXs(unittest.TestCase):

    # Tests comparing two strings of 1's and 0's
    def testStringsMatch10(self):
        self.assertEqual(compareWithXs("011010", "011010"), True)

    # Tests comparing two strings of 1's and 0's
    def testStringsFail10(self):
        self.assertEqual(compareWithXs("011110", "011010"), False)

    # Tests comparing two strings of 1's and 0's and x's
    def testStringsMatch10x(self):
        self.assertEqual(compareWithXs("01xxx0", "011010"), True)

    # Tests comparing two strings of 1's and 0's and x's
    def testStringsFail10x(self):
        self.assertEqual(compareWithXs("01xxx0", "011011"), False)

    # Tests differing length strings automatically fail
    def testStringsDiffLengths(self):
        self.assertEqual(compareWithXs("01101", "011010"), False)

class TestAliasCondCheck(unittest.TestCase):
    
    # Tests alias condition matching for a simple example
    def testSimpleCondition(self):
        values = tuple([("A", "1")]) # Matches how assignValues creates tuples

        self.assertEqual(aliasCondCheck("A == '1'", values), True)

    # Tests alias condition matching for a simple example
    def testSimpleConditionFail(self):
        values = tuple([("A", "1")]) # Matches how assignValues creates tuples

        self.assertEqual(aliasCondCheck("A == '0'", values), False)

    # Tests alias condition matching for an unconditional example
    def testUnconditionalCondition(self):
        values = tuple([("A", "1")]) # Matches how assignValues creates tuples

        self.assertEqual(aliasCondCheck("Unconditionally", values), True)

    # Tests alias condition matching for a never example
    def testNeverCondition(self):
        values = tuple([("A", "1")]) # Matches how assignValues creates tuples

        self.assertEqual(aliasCondCheck("Never", values), False)

    # Tests alias condition matching for an and example
    def testAndCondition(self):
        values = tuple([("A", "10110"), ("B", "111")]) # Matches how assignValues creates tuples

        self.assertEqual(aliasCondCheck("A == '10xx0' && B != '101'", values), True)

    # Tests alias condition f for an and example
    def testAndConditionFail(self):
        values = tuple([("A", "10110"), ("B", "111")]) # Matches how assignValues creates tuples

        self.assertEqual(aliasCondCheck("A == '10xx0' && B == '101'", values), False)

    # Tests alias condition matching for an or example
    def testOrCondition(self):
        values = tuple([("A", "10110"), ("B", "111")]) # Matches how assignValues creates tuples

        self.assertEqual(aliasCondCheck("A == '10xx0' || B != '111'", values), True)

    # Tests alias condition matching for an or example
    def testOrConditionFail(self):
        values = tuple([("A", "10110"), ("B", "111")]) # Matches how assignValues creates tuples

        self.assertEqual(aliasCondCheck("A == '10xx1' || B != '111'", values), False)

    # Tests alias condition matching for a complex example
    def testComplexCondition(self):
        values = tuple([("A", "10110"), ("B", "111"), ("C", "1"), ("D", "110")]) # Matches how assignValues creates tuples

        self.assertEqual(aliasCondCheck("A == '10110' && B == '11x' && (C != '1' || D == '1xx')", values), True)

    # Tests alias condition matching for a complex example
    def testComplexConditionFail(self):
        values = tuple([("A", "10110"), ("B", "111"), ("C", "1"), ("D", "010")]) # Matches how assignValues creates tuples

        self.assertEqual(aliasCondCheck("A == '10110' && B == '11x' && (C != '1' || D == '1xx')", values), False)

    #aliasCondCheck("S == '1' && Pn == '10x' && (S != '1' || Pn == '1xx')", (("S", 1), ("Pn", "101"), ("Pm", 100)))

class TestSplitWithBrackets(unittest.TestCase):

    # Tests that simple names are returned
    def testSimpleSplit(self):
        self.assertEqual(splitWithBrackets("imm5"), ["imm5"])

    # Tests that colons outside of angular brackets are split on
    def testConcatSplit(self):
        self.assertEqual(splitWithBrackets("imm5:imm4:imm3:imm2"), ["imm5", "imm4", "imm3", "imm2"])

    # Tests that colons inside angular brackets are not split on
    def testBracketsNotSplit(self):
        self.assertEqual(splitWithBrackets("imm5<4:3>"), ["imm5<4:3>"])

    # Tests that both types of colons are handled correctly in one call
    def testFullSplit(self):
        self.assertEqual(splitWithBrackets("imm5<4:3>:imm4<4>:imm3<28:4>"), ["imm5<4:3>", "imm4<4>", "imm3<28:4>"])

    # If a malformed pair of brackets, it will treat the colon as a concatenation and split on it
    def testNoClosing(self):
        self.assertEqual(splitWithBrackets("imm5<4:3"), ["imm5<4", "3"])

class TestCalculateConcatSymbols(unittest.TestCase):
    
    # Tests a basic substitution of a variable with its value
    def testBasicSymbol(self):
        values = tuple([("imm5", "10110"), ("imm4", "1101101"), ("imm3", "111"), ("imm2", "0100100")]) # Matches how assignValues creates tuples
        self.assertEqual(calculateConcatSymbols("imm5", values), "10110")

    # Tests concatentation works
    def testBasicSymbolConcat(self):
        values = tuple([("imm5", "10110"), ("imm4", "1101101"), ("imm3", "111"), ("imm2", "0100100")]) # Matches how assignValues creates tuples
        self.assertEqual(calculateConcatSymbols("imm5:imm4", values), "101101101101")

    # Tests extracting specific bits works
    def testBasicBrackets(self):
        values = tuple([("imm5", "10110"), ("imm4", "1101101"), ("imm3", "111"), ("imm2", "0100100")]) # Matches how assignValues creates tuples
        self.assertEqual(calculateConcatSymbols("imm5<2:0>", values), "110")

    # Tests more complex symbol encodings
    def testComplexEncoding(self):
        values = tuple([("imm5", "10110"), ("imm4", "1101101"), ("imm3", "111"), ("imm2", "0100100")]) # Matches how assignValues creates tuples
        self.assertEqual(calculateConcatSymbols("imm5<4:3>:imm4<5>:imm3<2:0>:imm2", values), "1011110100100")


    

if __name__ == '__main__':
    unittest.main()