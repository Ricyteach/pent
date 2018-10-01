r"""*Test objects for* ``pent`` *test suite*.

``pent`` Extracts Numerical Text.

**Author**
    Brian Skinn (bskinn@alum.mit.edu)

**File Created**
    3 Sep 2018

**Copyright**
    \(c) Brian Skinn 2018

**Source Repository**
    http://www.github.com/bskinn/pent

**Documentation**
    http://pent.readthedocs.io

**License**
    The MIT License; see |license_txt|_ for full license terms

**Members**

*(none documented)*

"""


import itertools as itt
from pathlib import Path
import re
import unittest as ut


# HELPERS
testdir_path = Path() / "pent" / "test"


class SuperPent:
    """Superclass of various test classes, with common methods."""

    @staticmethod
    def does_parse_match(re_pat, s):
        """Run match-or-not test on `s` using regex pattern `re_pat`."""
        m = re.search(re_pat, s)

        return m is not None

    @staticmethod
    def make_testname(v, n, s):
        """Compose test name from a numerical value and pattern Number/Sign."""
        return "{0}_{1}_{2}".format(v, n, s)


class TestPentCorePatterns(ut.TestCase, SuperPent):
    """Confirming basic pattern matching of the core regex patterns."""

    def test_number_and_sign_matching(self):
        """Confirm number and sign patterns match the right string patterns."""
        import pent

        from .testdata import number_sign_vals as vals

        for (v, n, s) in itt.product(vals, pent.Number, pent.Sign):
            with self.subTest(self.make_testname(v, n, s)):
                npat = pent.number_patterns[(n, s)]
                npat = pent.std_wordify(npat)

                res = self.does_parse_match(npat, v)

                self.assertEqual(vals[v][(n, s)], res, msg=npat)

    def test_raw_single_value_space_delimited(self):
        """Confirm single-value parsing from a line works with raw patterns."""
        import pent

        from .testdata import number_sign_vals as vals

        test_line = "This line contains the value {} with space delimit."

        for v in vals:
            test_str = test_line.format(v)

            for (n, s) in itt.product(pent.Number, pent.Sign):
                with self.subTest(self.make_testname(v, n, s)):
                    npat = pent.number_patterns[(n, s)]
                    npat = pent.std_wordify(npat)

                    res = self.does_parse_match(npat, test_str)

                    self.assertEqual(vals[v][(n, s)], res, msg=test_str)


class TestPentParserPatterns(ut.TestCase, SuperPent):
    """Confirming pattern matching of patterns generated by the Parser."""

    import pent

    prs = pent.Parser()

    def test_empty_pattern_matches_blank_line(self):
        """Confirm an empty pattern matches only a blank line."""
        import pent

        prs = pent.Parser(body="")

        self.assertIsNotNone(re.search(prs.pattern(), ""))
        self.assertIsNone(re.search(prs.pattern(), "3"))

    def test_group_tags_or_not(self):
        """Confirm group tags are added when needed; omitted when not."""
        import pent

        patterns = {
            pent.Content.Any: "~{}",
            pent.Content.String: "@{}.this",
            pent.Content.Number: "#{}..g",
        }

        for content, capture in itt.product(pent.Content, (True, False)):
            test_name = "{0}_{1}".format(content, capture)
            with self.subTest(test_name):
                test_pat = patterns[content].format("!" if capture else "")
                test_rx = self.prs.convert_line(test_pat)[0]
                self.assertEqual(capture, "(?P<" in test_rx, msg=test_pat)

    def test_parser_single_line_space_delim(self):
        """Confirm parser works on single lines with space-delimited values.

        Also tests the 'suppress' number mode.

        """
        import pent

        from .testdata import number_sign_vals as vals

        test_line = "This line contains the value {} with space delimit."
        test_pat_template = "~ @!.contains ~! #!.{0}{1} ~"

        for v in vals:
            test_str = test_line.format(v)

            for (n, s) in itt.product(pent.Number, pent.Sign):
                test_pat = test_pat_template.format(s.value, n.value)

                with self.subTest(self.make_testname(v, n, s)):
                    npat = self.prs.convert_line(test_pat)[0]

                    res = self.does_parse_match(npat, test_str)

                    self.assertEqual(vals[v][n, s], res, msg=test_str)

    def test_string_capture(self):
        """Confirm string capture works when desired; is ignored when not."""
        import pent

        test_line = "This is a string with a word and [symbol] in it."
        test_pat_capture = "~ @!.word ~"
        test_pat_ignore = "~ @.word ~"
        test_pat_symbol = "~ @!.[symbol] ~"
        test_pat_with_space = "~ '@!.string with' ~"

        with self.subTest("capture"):
            pat = self.prs.convert_line(test_pat_capture)[0]
            m = re.search(pat, test_line)
            self.assertIsNotNone(m)
            self.assertEqual(m.group(pent.Token.group_prefix + "0"), "word")

        with self.subTest("ignore"):
            pat = self.prs.convert_line(test_pat_ignore)[0]
            m = re.search(pat, test_line)
            self.assertIsNotNone(m)
            self.assertRaises(
                IndexError, m.group, pent.Token.group_prefix + "0"
            )

        with self.subTest("symbol"):
            pat = self.prs.convert_line(test_pat_symbol)[0]
            m = re.search(pat, test_line)
            self.assertIsNotNone(m)
            self.assertEqual(
                m.group(pent.Token.group_prefix + "0"), "[symbol]"
            )

        with self.subTest("with_space"):
            pat = self.prs.convert_line(test_pat_with_space)[0]
            m = re.search(pat, test_line)
            self.assertIsNotNone(m)
            self.assertEqual(
                m.group(pent.Token.group_prefix + "0"), "string with"
            )

    def test_single_num_capture(self):
        """Confirm single-number capture works."""
        import pent

        from .testdata import number_sign_vals as vals

        test_line = "This is a string with {} in it."
        test_pat_template = "~ #!.{0}{1} ~"

        for v in vals:
            test_str = test_line.format(v)

            for (n, s) in itt.product(pent.Number, pent.Sign):
                test_pat = test_pat_template.format(s.value, n.value)

                with self.subTest(self.make_testname(v, n, s)):
                    npat = self.prs.convert_line(test_pat)[0]

                    m = re.search(npat, test_str)

                    self.assertEqual(
                        vals[v][n, s], m is not None, msg=test_str
                    )

                    if m is not None:
                        self.assertEqual(
                            m.group(pent.Token.group_prefix + "0"), v
                        )

    def test_single_nums_no_space(self):
        """Confirm two-number capture works, with no intervening space.

        Not a particularly real-world test-case, but it probes the
        no-space-before check.

        """
        import pent

        test_str = "This is a string with 123-456 in it."
        test_pat = "~ #x!.+i #!.-i ~"

        npat = self.prs.convert_line(test_pat)[0]

        m = re.search(npat, test_str)

        self.assertIsNotNone(m)
        self.assertEqual(m.group(pent.Token.group_prefix + "0"), "123")
        self.assertEqual(m.group(pent.Token.group_prefix + "1"), "-456")

    def test_single_num_preceding_colon_capture(self):
        """Confirm single-number capture works, with preceding colon."""
        import pent

        from .testdata import number_sign_vals as vals

        test_line = "This is a string with :{} in it, after a colon."
        test_pat_template = "~ @x.: #!.{0}{1} ~"

        for v in vals:
            test_str = test_line.format(v)

            for (n, s) in itt.product(pent.Number, pent.Sign):
                test_pat = test_pat_template.format(s.value, n.value)

                with self.subTest(self.make_testname(v, n, s)):
                    npat = self.prs.convert_line(test_pat)[0]

                    m = re.search(npat, test_str)

                    self.assertEqual(
                        vals[v][n, s], m is not None, msg=test_str
                    )

                    if m is not None:
                        self.assertEqual(
                            m.group(pent.Token.group_prefix + "0"), v
                        )

    def test_string_and_single_num_capture(self):
        """Confirm multiple capture of string and single number."""
        import pent

        from .testdata import number_sign_vals as vals

        test_line = "This is a string with {} in it."
        test_pat_template = "~ @!.string ~ #!.{0}{1} ~"

        for v in vals:
            test_str = test_line.format(v)

            for (n, s) in itt.product(pent.Number, pent.Sign):
                test_pat = test_pat_template.format(s.value, n.value)

                with self.subTest(self.make_testname(v, n, s)):
                    npat = self.prs.convert_line(test_pat)[0]

                    m = re.search(npat, test_str)

                    self.assertEqual(
                        vals[v][n, s], m is not None, msg=test_str
                    )

                    if m is not None:
                        self.assertEqual(
                            m.group(pent.Token.group_prefix + "0"), "string"
                        )
                        self.assertEqual(
                            m.group(pent.Token.group_prefix + "1"), v
                        )

    def test_number_ending_sentence(self):
        """Check that a number at the end of a sentence matches correctly."""
        import pent

        from .testdata import number_patterns as npats

        test_line = "This sentence ends with a number {}."
        test_pat = "~ {} @.."

        for n in npats:
            token = npats[n].format(
                pent.SpaceAfter.Prohibited,
                pent.Token._s_capture,
                pent.Quantity.Single,
            )
            with self.subTest(token):
                pat = self.prs.convert_line(test_pat.format(token))[0]
                m = re.search(pat, test_line.format(n))

                self.assertIsNotNone(m, msg=test_line.format(n) + token)
                self.assertEqual(n, m.group(pent.Token.group_prefix + "0"))

    def test_match_entire_line(self):
        """Confirm the tilde works to match an entire line."""
        import pent

        test_line = "This is a line with whatever weird (*#$(*&23646{}}{#$"

        with self.subTest("capture"):
            pat = self.prs.convert_line("~!")[0]
            self.assertTrue(self.does_parse_match(pat, test_line))

            m = re.search(pat, test_line)
            self.assertEqual(test_line, m.group(pent.Token.group_prefix + "0"))

        with self.subTest("no_capture"):
            pat = self.prs.convert_line("~")[0]
            self.assertTrue(self.does_parse_match(pat, test_line))

            m = re.search(pat, test_line)
            self.assertRaises(
                IndexError, m.group, pent.Token.group_prefix + "0"
            )

    def test_any_token_capture_ranges(self):
        """Confirm 'any' captures work as expected with other tokens."""
        import pent

        test_line_start = "This is a line "
        test_line_end = " with a number in brackets in the middle."
        test_num = "2e-4"
        test_line = test_line_start + "[" + test_num + "]" + test_line_end

        pat = pent.Parser().convert_line("~! @x.[ #x!..g @x.] ~!")[0]
        m = re.search(pat, test_line)

        self.assertEqual(
            m.group(pent.Token.group_prefix + "0"), test_line_start
        )
        self.assertEqual(m.group(pent.Token.group_prefix + "1"), test_num)
        self.assertEqual(m.group(pent.Token.group_prefix + "2"), test_line_end)

    @ut.skip("Developing without optional/zero-or-more for now")
    def test_optional_str(self):
        """Confirm single optional str token works as expected."""
        import pent

        test_string = "This is a test {} string."
        test_pat = "~ @.test @{}?foo @x.string ~"

        for there, cap in itt.product(*itt.repeat((True, False), 2)):
            with self.subTest("There: {0}, Cap: {1}".format(there, cap)):
                pat = test_pat.format(pent.Token._s_capture if cap else "")
                prs_pat = pent.Parser().convert_line(pat)[0]

                work_str = test_string.format("foo" if there else "")

                m = re.search(prs_pat, work_str)

                self.assertIsNotNone(m)
                if cap:
                    if there:
                        self.assertEqual(
                            "foo",
                            m.group(pent.Token.group_prefix + "0"),
                            msg=work_str + pat,
                        )
                    else:
                        self.assertEqual(
                            "", m.group(pent.Token.group_prefix + "0")
                        )
                else:
                    self.assertRaises(
                        IndexError, m.group, pent.Token.group_prefix + "0"
                    )

    def test_one_or_more_str_nospace(self):
        """Confirm one-or-more str token works as expected w/no space."""
        import pent

        test_string = "This is a test {} string."
        test_pat = "~ @{}+foo ~"

        for qty, cap in itt.product((1, 2, 3), (True, False)):
            with self.subTest("Qty: {0}, Cap: {1}".format(qty, cap)):
                pat = test_pat.format(pent.Token._s_capture if cap else "")
                pat = pent.Parser().convert_line(pat)[0]

                work_str = test_string.format("foo" * qty)

                m = re.search(pat, work_str)

                self.assertIsNotNone(m)
                if cap:
                    self.assertEqual(
                        "foo" * qty, m.group(pent.Token.group_prefix + "0")
                    )
                else:
                    self.assertRaises(
                        IndexError, m.group, pent.Token.group_prefix + "0"
                    )

    def test_one_or_more_str_with_space(self):
        """Confirm one-or-more str token works as expected w/space."""
        import pent

        test_string = "This is a test {}string."
        test_pat = "~ '@x{}+foo ' ~"

        for qty, cap in itt.product((1, 2, 3), (True, False)):
            with self.subTest("Qty: {0}, Cap: {1}".format(qty, cap)):
                pat = test_pat.format(pent.Token._s_capture if cap else "")
                pat = pent.Parser().convert_line(pat)[0]

                work_str = test_string.format("foo " * qty)

                m = re.search(pat, work_str)

                self.assertIsNotNone(m)
                if cap:
                    self.assertEqual(
                        "foo " * qty, m.group(pent.Token.group_prefix + "0")
                    )
                else:
                    self.assertRaises(
                        IndexError, m.group, pent.Token.group_prefix + "0"
                    )

    @ut.skip("Skipping until resolve Optional.")
    def test_zero_or_more_str(self):
        """Confirm zero-or-more str token works as expected."""
        import pent

        test_string = "This is a test {}string."
        test_pat = "~ @{}*foo ~"

        for qty, cap in itt.product((0, 1, 2, 3), (True, False)):
            with self.subTest("Qty: {0}, Cap: {1}".format(qty, cap)):
                pat = test_pat.format(pent.Token._s_capture if cap else "")
                pat = pent.Parser().convert_line(pat)[0]

                work_str = test_string.format("foo " * qty)

                m = re.search(pat, work_str)

                self.assertIsNotNone(m)
                if cap:
                    self.assertEqual(
                        "foo " * qty, m.group(pent.Token.group_prefix + "0")
                    )
                else:
                    self.assertRaises(
                        IndexError, m.group, pent.Token.group_prefix + "0"
                    )

    @ut.skip("Developing w/o optional/zero-or-more for now")
    def test_one_or_more_doesnt_match_zero_reps(self):
        """Confirm one-or-more str doesn't match if string isn't there."""
        import pent

        test_string = "This is  a test string."
        test_pat = "~ @.is @!?absolutely @.a ~"

        m = re.search(self.prs.convert_line(test_pat)[0], test_string)

        self.assertEqual("", m.group(pent.Token.group_prefix + "0"))

    def test_manual_two_lines(self):
        """Run manual check on concatenating two single-line regexes."""
        import pent

        test_str = "This is line one: 12345  \nAnd this is line two: -3e-5"

        test_pat_1 = "~ @!.one: #!.+i"
        test_pat_2 = "~ @!.two: #!.-s"

        cp_1 = self.prs.convert_line(test_pat_1)[0]
        cp_2 = self.prs.convert_line(test_pat_2, group_id=2)[0]

        m = re.search(cp_1 + r"\n" + cp_2, test_str)

        self.assertIsNotNone(m)
        self.assertEqual("one:", m.group(pent.Token.group_prefix + "0"))
        self.assertEqual("12345", m.group(pent.Token.group_prefix + "1"))
        self.assertEqual("two:", m.group(pent.Token.group_prefix + "2"))
        self.assertEqual("-3e-5", m.group(pent.Token.group_prefix + "3"))

    def test_quick_one_or_more_number(self):
        """Run quick check on capture of one-or-more number token."""
        import pent

        numbers = "2 5 -54 3.8 -1.e-12"

        test_str = "This has numbers {} with end space.".format(numbers)
        test_str_period = "This has numbers {}.".format(numbers)

        test_pat = "~ #!+.g ~"
        test_pat_period = "~ #x!+.g @.."

        re_pat = self.prs.convert_line(test_pat)[0]
        re_pat_period = self.prs.convert_line(test_pat_period)[0]

        with self.subTest("end_space"):
            m_pat = re.search(re_pat, test_str)
            self.assertIsNotNone(m_pat)
            self.assertEqual(
                m_pat.group(pent.Token.group_prefix + "0"), numbers
            )

        with self.subTest("period"):
            m_pat_period = re.search(re_pat_period, test_str_period)
            self.assertIsNotNone(m_pat_period)
            self.assertEqual(
                m_pat_period.group(pent.Token.group_prefix + "0"), numbers
            )

    def test_multiline_body_parser(self):
        """Confirm parsing w/multi-line body works ok."""
        import pent

        result = [[["1", "2", "4"]]]

        text = "\n1\n\n2\n\n\n4"

        pat = ("", "#!.+i", "", "#!.+i", "", "", "#!.+i")
        prs = pent.Parser(body=pat)

        self.assertEqual(prs.capture_body(text), result)
        
    def test_optional_space_after_literal(self):
        """Confirm the optional-space matching works."""
        from textwrap import dedent
        
        import pent
        
        text = dedent("""\
            1 2 3 4 5
            VALUE= 1
            VALUE= 2 
            VALUE=10""")
        
        result = [[['1'], ['2'], ['10']]]
        
        fail_prs = pent.Parser(head="#++i", body="@.VALUE= #!..i")
        good_prs = pent.Parser(head="#++i", body="@o.VALUE= #!..i")
        
        self.assertNotEqual(result, fail_prs.capture_body(text))
        self.assertEqual(result, good_prs.capture_body(text))
    
    def test_optional_space_after_number(self):
        """Confirm optional-space works for after numbers."""
        from textwrap import dedent
        
        import pent
        
        text = dedent("""
            1 2 3 4 5
            23 .
            23.
            -3e4 .
            -3e4.
            """)
        
        result = [[['23'], ['23'], ['-3e4'], ['-3e4']]]
        
        good_prs = pent.Parser(head="#++i", body="#o!..g @..")
        fail_prs = pent.Parser(head="#++i", body="#!..g @..")
        
        self.assertNotEqual(result, fail_prs.capture_body(text))
        self.assertEqual(result, good_prs.capture_body(text))

    def test_orca_hess_freq_parser(self):
        """Confirm 1-D data parser for ORCA freqs works."""
        import pent

        from .testdata import orca_hess_freqs

        head_pattern = ("@.$vibrational_frequencies", "#!.+i")
        body_pattern = "#.+i #!..f"

        # Trivial application of the tail, but serves to check that
        # it works correctly.
        tail_pattern = ("~", "@.$normal_modes", "#!++i")

        file_path = str(testdir_path / "C2F4_01.hess")

        freq_parser = pent.Parser(
            head=head_pattern, body=body_pattern, tail=tail_pattern
        )

        with open(file_path) as f:
            data = f.read()

        m = re.search(freq_parser.pattern(), data)
        self.assertIsNotNone(m)
        self.assertEqual(m.group(0).count("\n"), 22)

        self.assertEqual(freq_parser.capture_head(data), ["18"])
        self.assertEqual(freq_parser.capture_tail(data), ["18", "18"])

        self.assertEqual(freq_parser.capture_body(data), orca_hess_freqs)

    def test_orca_hess_dipders_parser(self):
        """Confirm 2-D single-block data parser for ORCA dipders works."""
        import pent

        from .testdata import orca_hess_dipders

        head_pattern = ("@.$dipole_derivatives", "#.+i")
        body_pattern = "#!+.f"

        file_path = str(testdir_path / "C2F4_01.hess")

        freq_parser = pent.Parser(head=head_pattern, body=body_pattern)

        with open(file_path) as f:
            data = f.read()

        self.assertEqual(freq_parser.capture_body(data), orca_hess_dipders)

    def test_simple_multiblock(self):
        """Confirm simple multiblock parser works correctly."""
        from textwrap import dedent

        import pent

        from .testdata import mblock_result

        data = dedent(
            """
               test

               more test

               $data
                      1      2      3
                  1   2.5   -3.5    0.8
                  2  -1.2    8.1   -9.2

                      4      5      6
                  1  -0.1    3.5    8.1
                  2   1.4    2.2   -4.7

               $next_data"""
        )

        prs_inner = pent.Parser(head="#++i", body="#.+i #!+.f", tail="")
        prs_outer = pent.Parser(head="@.$data", body=prs_inner)

        self.assertEqual(prs_outer.capture_body(data), mblock_result)

    def test_repeated_multiblock(self):
        """Confirm repeated multiblock parser works correctly."""
        from textwrap import dedent

        import pent

        from .testdata import mblock_repeated_result

        data = dedent(
            """
            $top
                1     2     3
                0.2   0.3   0.4
                0.3   0.4   0.6
                4     5     6
                0.1   0.1   0.1
                0.5   0.5   0.5

            $top
                7     8     9
                0.2   0.2   0.2
                0.6   0.6   0.6
                1     2     3
                0.4   0.4   0.4
                0.8   0.8   0.8
        """
        )

        prs_inner = pent.Parser(head="#++i", body="#!+.f")
        prs_outer = pent.Parser(head="@.$top", body=prs_inner)

        self.assertEqual(prs_outer.capture_body(data), mblock_repeated_result)


class TestPentTokens(ut.TestCase, SuperPent):
    """Direct tests on the Token class."""

    def test_arbitrary_bad_token(self):
        """Confirm bad tokens raise errors."""
        import pent

        self.assertRaises(pent.TokenError, pent.Token, "abcd")

    def test_group_enclosures(self):
        """Ensure 'ignore' flag is properly set."""
        import pent

        testname_fmt = "{0}_{1}"
        token_fmt = {
            pent.Content.Any: "~{0}",
            pent.Content.String: "@{0}.thing",
            pent.Content.Number: "#{0}..i",
        }

        for ct, cap in itt.product(pent.Content, (True, False)):
            t = pent.Token(token_fmt[ct].format("!" if cap else ""))
            with self.subTest(testname_fmt.format(ct, cap)):
                self.assertEqual(t.capture, cap)

    def test_number_property(self):
        """Ensure t.number properties return correct values."""
        import pent

        from .testdata import number_patterns as npats

        for p in npats.values():
            pat = p.format("", "", pent.Quantity.Single)
            with self.subTest(pat):
                self.assertEqual(pent.Token(pat).number, pent.Number(p[-1]))

        with self.subTest("string"):
            self.assertEqual(pent.Token("@.abcd").number, None)

        with self.subTest("any"):
            self.assertEqual(pent.Token("~").number, None)

    def test_sign_property(self):
        """Ensure t.sign properties return correct values."""
        import pent

        from .testdata import number_patterns as npats

        for p in npats.values():
            pat = p.format("", "", pent.Quantity.Single)
            with self.subTest(pat):
                self.assertEqual(pent.Token(pat).sign, pent.Sign(p[-2]))

        with self.subTest("string"):
            self.assertEqual(pent.Token("@.abcd").sign, None)

        with self.subTest("any"):
            self.assertEqual(pent.Token("~").sign, None)

    def test_qty_property_on_any(self):
        """Ensure t.match_quantity property returns correct value on 'any'."""
        import pent

        self.assertEqual(pent.Token("~").match_quantity, None)


class TestPentParserPatternsSlow(ut.TestCase, SuperPent):
    """SLOW tests confirming pattern matching of Parser regexes."""

    import pent

    prs = pent.Parser()

    def test_three_token_sequence(self):
        """Ensure combinatorial token sequence parses correctly."""
        import pent

        from .testdata import number_patterns as nps

        pat_template = "~ {0} {1} {2} ~"
        str_template = "String! {0}{1}{2}{3}{4} More String!"
        str_pat = {"foo": "@{0}{1}{2}foo"}

        testname_template = "{0}_{1}_{2}_{3}_{4}"

        str_or_num = (pent.Content.String, pent.Content.Number)
        t_f = (True, False)

        for c1, s1, c2, s2, c3 in itt.product(
            str_or_num, t_f, str_or_num, t_f, str_or_num
        ):
            if (c1 is c2 and not s1) or (c2 is c3 and not s2):
                # No reason to have no-space strings against one another;
                # no-space numbers adjacent to one another make
                # no syntactic sense.
                continue

            vals1 = str_pat if c1 == pent.Content.String else nps.keys()
            vals2 = str_pat if c2 == pent.Content.String else nps.keys()
            vals3 = str_pat if c3 == pent.Content.String else nps.keys()

            for v1, v2, v3 in itt.product(vals1, vals2, vals3):
                p1 = (str_pat if c1 == pent.Content.String else nps)[
                    v1
                ].format(
                    pent.Token._s_no_space if not s1 else "",
                    pent.Token._s_capture,
                    pent.Quantity.Single,
                )
                p2 = (str_pat if c2 == pent.Content.String else nps)[
                    v2
                ].format(
                    pent.Token._s_no_space if not s2 else "",
                    pent.Token._s_capture,
                    pent.Quantity.Single,
                )
                p3 = (str_pat if c3 == pent.Content.String else nps)[
                    v3
                ].format("", pent.Token._s_capture, pent.Quantity.Single)

                test_pat = pat_template.format(p1, p2, p3)
                test_str = str_template.format(
                    v1, " " if s1 else "", v2, " " if s2 else "", v3
                )

                with self.subTest(
                    testname_template.format(v1, s1, v2, s2, v3)
                ):
                    npat = self.prs.convert_line(test_pat)[0]

                    m = re.search(npat, test_str)

                    self.assertIsNotNone(m, msg=test_pat)
                    self.assertEqual(
                        m.group(pent.Token.group_prefix + "0"),
                        v1,
                        msg=test_pat + " :: " + test_str,
                    )
                    self.assertEqual(
                        m.group(pent.Token.group_prefix + "1"),
                        v2,
                        msg=test_pat + " :: " + test_str,
                    )
                    self.assertEqual(
                        m.group(pent.Token.group_prefix + "2"),
                        v3,
                        msg=test_pat + " :: " + test_str,
                    )


def suite_base():
    """Create and return the test suite for base tests."""
    s = ut.TestSuite()
    tl = ut.TestLoader()
    s.addTests(
        [
            tl.loadTestsFromTestCase(TestPentCorePatterns),
            tl.loadTestsFromTestCase(TestPentParserPatterns),
            tl.loadTestsFromTestCase(TestPentTokens),
        ]
    )
    return s


def suite_base_slow():
    """Create and return the test suite for SLOW base tests."""
    s = ut.TestSuite()
    tl = ut.TestLoader()
    s.addTests([tl.loadTestsFromTestCase(TestPentParserPatternsSlow)])
    return s


if __name__ == "__main__":
    print("Module not executable.")
