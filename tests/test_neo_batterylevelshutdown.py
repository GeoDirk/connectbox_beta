#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `neo_batterylevelshutdown` package."""


import unittest
from click.testing import CliRunner

from neo_batterylevelshutdown import cli


class TestNeo_batterylevelshutdown(unittest.TestCase):
    """Tests for `neo_batterylevelshutdown` package."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_first_test(self):
        """Test something."""
        self.assertTrue(True)

    @unittest.skip("--help not implemented yet")
    def test_command_line_interface(self):
        """Test the CLI."""
        runner = CliRunner()
        result = runner.invoke(cli.main)
        assert result.exit_code == 0
        assert 'neo_batterylevelshutdown.cli.main' in result.output
        help_result = runner.invoke(cli.main, ['--help'])
        assert help_result.exit_code == 0
        assert '--help  Show this message and exit.' in help_result.output
