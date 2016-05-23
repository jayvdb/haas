# -*- coding: utf-8 -*-
# Copyright (c) 2013-2014 Simon Jagoe
# All rights reserved.
#
# This software may be modified and distributed under the terms
# of the 3-clause BSD license.  See the LICENSE.txt file for details.
from __future__ import absolute_import, unicode_literals

from contextlib import contextmanager
from datetime import datetime, timedelta
from time import ctime
import sys

from mock import Mock, patch
from six.moves import StringIO

from ..plugins.i_result_handler_plugin import IResultHandlerPlugin
from ..plugins.result_handler import (
    QuietTestResultHandler, StandardTestResultHandler,
    VerboseTestResultHandler)
from ..result import (
    ResultCollecter, TestResult, TestCompletionStatus, TestDuration)
from ..testing import unittest
from . import _test_cases, _test_case_data
from .mocks import MockDateTime


class ExcInfoFixture(object):

    @contextmanager
    def failure_exc_info(self, msg=None):
        try:
            self.fail(msg)
        except self.failureException:
            yield sys.exc_info()

    @contextmanager
    def exc_info(self, cls):
        try:
            raise cls()
        except cls:
            yield sys.exc_info()


class TestTextTestResult(ExcInfoFixture, unittest.TestCase):

    def test_result_collector_calls_handlers_start_stop_methods(self):
        # Given
        handler = Mock(spec=IResultHandlerPlugin)
        collector = ResultCollecter()
        collector.add_result_handler(handler)
        case = _test_cases.TestCase('test_method')

        # When
        handler.reset_mock()
        collector.startTestRun()

        # Then
        handler.start_test_run.assert_called_once_with()
        self.assertFalse(handler.called)
        self.assertFalse(handler.stop_test_run.called)
        self.assertFalse(handler.start_test.called)
        self.assertFalse(handler.stop_test.called)

        # When
        handler.reset_mock()
        collector.stopTestRun()

        # Then
        handler.stop_test_run.assert_called_once_with()
        self.assertFalse(handler.called)
        self.assertFalse(handler.start_test_run.called)
        self.assertFalse(handler.start_test.called)
        self.assertFalse(handler.stop_test.called)

        # When
        handler.reset_mock()
        collector.startTest(case)

        # Then
        handler.start_test.assert_called_once_with(case)
        self.assertFalse(handler.called)
        self.assertFalse(handler.start_test_run.called)
        self.assertFalse(handler.stop_test_run.called)
        self.assertFalse(handler.stop_test.called)

        # When
        handler.reset_mock()
        collector.stopTest(case)

        # Then
        handler.stop_test.assert_called_once_with(case)
        self.assertFalse(handler.called)
        self.assertFalse(handler.start_test_run.called)
        self.assertFalse(handler.stop_test_run.called)
        self.assertFalse(handler.start_test.called)

    def test_unicode_traceback(self):
        # Given
        handler = Mock(spec=IResultHandlerPlugin)
        collector = ResultCollecter()
        collector.add_result_handler(handler)
        start_time = datetime(2015, 12, 23, 8, 14, 12)
        duration = timedelta(seconds=10)
        end_time = start_time + duration
        expected_duration = TestDuration(start_time, end_time)
        case = _test_cases.TestCase('test_method')

        # When
        with patch('haas.result.datetime', new=MockDateTime(start_time)):
            collector.startTest(case)

        # Then
        self.assertTrue(handler.start_test.called)
        handler.start_test.reset_mock()

        # Given
        msg = '\N{GREEK SMALL LETTER PHI}'.encode('utf-8')
        with self.failure_exc_info(msg) as exc_info:
            expected_result = TestResult.from_test_case(
                case, TestCompletionStatus.error, expected_duration,
                exception=exc_info)
            # When
            with patch('haas.result.datetime', new=MockDateTime(end_time)):
                collector.addError(case, exc_info)

        # Then
        handler.assert_called_once_with(expected_result)
        self.assertFalse(handler.start_test_run.called)
        self.assertFalse(handler.stop_test_run.called)
        self.assertFalse(handler.start_test.called)
        self.assertFalse(handler.stop_test.called)
        self.assertFalse(collector.wasSuccessful())

    def test_result_collector_calls_handlers_on_error(self):
        # Given
        handler = Mock(spec=IResultHandlerPlugin)
        collector = ResultCollecter()
        collector.add_result_handler(handler)
        start_time = datetime(2015, 12, 23, 8, 14, 12)
        duration = timedelta(seconds=10)
        end_time = start_time + duration
        expected_duration = TestDuration(start_time, end_time)
        case = _test_cases.TestCase('test_method')

        # When
        with patch('haas.result.datetime', new=MockDateTime(start_time)):
            collector.startTest(case)

        # Then
        self.assertTrue(handler.start_test.called)
        handler.start_test.reset_mock()

        # When
        with self.exc_info(RuntimeError) as exc_info:
            # Given
            expected_result = TestResult.from_test_case(
                case, TestCompletionStatus.error, expected_duration,
                exception=exc_info)

            # When
            with patch('haas.result.datetime', new=MockDateTime(end_time)):
                collector.addError(case, exc_info)

        # Then
        handler.assert_called_once_with(expected_result)
        self.assertFalse(handler.start_test_run.called)
        self.assertFalse(handler.stop_test_run.called)
        self.assertFalse(handler.start_test.called)
        self.assertFalse(handler.stop_test.called)
        self.assertFalse(collector.wasSuccessful())

    def test_result_collector_calls_handlers_on_failure(self):
        # Given
        handler = Mock(spec=IResultHandlerPlugin)
        collector = ResultCollecter()
        collector.add_result_handler(handler)
        start_time = datetime(2015, 12, 23, 8, 14, 12)
        duration = timedelta(seconds=10)
        end_time = start_time + duration
        expected_duration = TestDuration(start_time, end_time)
        case = _test_cases.TestCase('test_method')

        # When
        with patch('haas.result.datetime', new=MockDateTime(start_time)):
            collector.startTest(case)

        # Then
        self.assertTrue(handler.start_test.called)
        handler.start_test.reset_mock()

        # Given
        with self.failure_exc_info() as exc_info:
            expected_result = TestResult.from_test_case(
                case, TestCompletionStatus.failure, expected_duration,
                exception=exc_info)

            # When
            with patch('haas.result.datetime', new=MockDateTime(end_time)):
                collector.addFailure(case, exc_info)

        # Then
        handler.assert_called_once_with(expected_result)
        self.assertFalse(handler.start_test_run.called)
        self.assertFalse(handler.stop_test_run.called)
        self.assertFalse(handler.start_test.called)
        self.assertFalse(handler.stop_test.called)
        self.assertFalse(collector.wasSuccessful())

    def test_result_collector_calls_handlers_on_success(self):
        # Given
        handler = Mock(spec=IResultHandlerPlugin)
        collector = ResultCollecter()
        collector.add_result_handler(handler)
        start_time = datetime(2015, 12, 23, 8, 14, 12)
        duration = timedelta(seconds=10)
        end_time = start_time + duration
        expected_duration = TestDuration(start_time, end_time)
        case = _test_cases.TestCase('test_method')

        # When
        with patch('haas.result.datetime', new=MockDateTime(start_time)):
            collector.startTest(case)

        # Then
        self.assertTrue(handler.start_test.called)
        handler.start_test.reset_mock()

        # Given
        expected_result = TestResult.from_test_case(
            case, TestCompletionStatus.success, expected_duration)

        # When
        with patch('haas.result.datetime', new=MockDateTime(end_time)):
            collector.addSuccess(case)

        # Then
        handler.assert_called_once_with(expected_result)
        self.assertFalse(handler.start_test_run.called)
        self.assertFalse(handler.stop_test_run.called)
        self.assertFalse(handler.start_test.called)
        self.assertFalse(handler.stop_test.called)
        self.assertTrue(collector.wasSuccessful())

    def test_result_collector_calls_handlers_on_skip(self):
        # Given
        handler = Mock(spec=IResultHandlerPlugin)
        collector = ResultCollecter()
        collector.add_result_handler(handler)
        start_time = datetime(2015, 12, 23, 8, 14, 12)
        duration = timedelta(seconds=10)
        end_time = start_time + duration
        expected_duration = TestDuration(start_time, end_time)
        case = _test_cases.TestCase('test_method')

        # When
        with patch('haas.result.datetime', new=MockDateTime(start_time)):
            collector.startTest(case)

        # Then
        self.assertTrue(handler.start_test.called)
        handler.start_test.reset_mock()

        # Given
        expected_result = TestResult.from_test_case(
            case, TestCompletionStatus.skipped, expected_duration,
            message='reason')

        # When
        with patch('haas.result.datetime', new=MockDateTime(end_time)):
            collector.addSkip(case, 'reason')

        # Then
        handler.assert_called_once_with(expected_result)
        self.assertFalse(handler.start_test_run.called)
        self.assertFalse(handler.stop_test_run.called)
        self.assertFalse(handler.start_test.called)
        self.assertFalse(handler.stop_test.called)
        self.assertTrue(collector.wasSuccessful())

    def test_result_collector_calls_handlers_on_expected_fail(self):
        # Given
        handler = Mock(spec=IResultHandlerPlugin)
        collector = ResultCollecter()
        collector.add_result_handler(handler)
        start_time = datetime(2015, 12, 23, 8, 14, 12)
        duration = timedelta(seconds=10)
        end_time = start_time + duration
        expected_duration = TestDuration(start_time, end_time)
        case = _test_cases.TestCase('test_method')

        # When
        with patch('haas.result.datetime', new=MockDateTime(start_time)):
            collector.startTest(case)

        # Then
        self.assertTrue(handler.start_test.called)
        handler.start_test.reset_mock()

        # Given
        with self.exc_info(RuntimeError) as exc_info:
            expected_result = TestResult.from_test_case(
                case, TestCompletionStatus.expected_failure, expected_duration,
                exception=exc_info)

            # When
            with patch('haas.result.datetime', new=MockDateTime(end_time)):
                collector.addExpectedFailure(case, exc_info)

        # Then
        handler.assert_called_once_with(expected_result)
        self.assertFalse(handler.start_test_run.called)
        self.assertFalse(handler.stop_test_run.called)
        self.assertFalse(handler.start_test.called)
        self.assertFalse(handler.stop_test.called)
        self.assertTrue(collector.wasSuccessful())

    def test_result_collector_calls_handlers_on_unexpected_success(self):
        # Given
        handler = Mock(spec=IResultHandlerPlugin)
        collector = ResultCollecter()
        collector.add_result_handler(handler)
        start_time = datetime(2015, 12, 23, 8, 14, 12)
        duration = timedelta(seconds=10)
        end_time = start_time + duration
        expected_duration = TestDuration(start_time, end_time)
        case = _test_cases.TestCase('test_method')

        # When
        with patch('haas.result.datetime', new=MockDateTime(start_time)):
            collector.startTest(case)

        # Then
        self.assertTrue(handler.start_test.called)
        handler.start_test.reset_mock()

        # Given
        expected_result = TestResult.from_test_case(
            case, TestCompletionStatus.unexpected_success, expected_duration)

        # When
        with patch('haas.result.datetime', new=MockDateTime(end_time)):
            collector.addUnexpectedSuccess(case)

        # Then
        handler.assert_called_once_with(expected_result)
        self.assertFalse(handler.start_test_run.called)
        self.assertFalse(handler.stop_test_run.called)
        self.assertFalse(handler.start_test.called)
        self.assertFalse(handler.stop_test.called)
        self.assertFalse(collector.wasSuccessful())

    def test_result_collector_should_stop(self):
        # Given
        collector = ResultCollecter()

        # Then
        self.assertFalse(collector.shouldStop)

        # When
        collector.stop()

        # Then
        self.assertTrue(collector.shouldStop)

    def test_multiple_errors_from_one_test(self):
        # Given
        collector = ResultCollecter()
        case = _test_case_data.TestWithTwoErrors('test_with_two_errors')

        start_time = datetime(2016, 4, 12, 8, 17, 32)
        test_end_time = datetime(2016, 4, 12, 8, 17, 38)
        tear_down_end_time = datetime(2016, 4, 12, 8, 17, 39)

        # When
        with patch('haas.result.datetime',
                   new=MockDateTime([start_time, test_end_time,
                                     tear_down_end_time])):
            case.run(collector)

        # Then
        self.assertEqual(len(collector.errors), 2)


class TestFailfast(ExcInfoFixture, unittest.TestCase):

    def test_failfast_enabled_on_error(self):
        # Given
        collector = ResultCollecter(failfast=True)
        self.assertFalse(collector.shouldStop)
        case = _test_cases.TestCase('test_method')

        collector.startTest(case)

        # When
        with self.exc_info(RuntimeError) as exc_info:
            collector.addError(case, exc_info)

        # Then
        self.assertTrue(collector.shouldStop)

    def test_failfast_enabled_on_failure(self):
        # Given
        collector = ResultCollecter(failfast=True)
        self.assertFalse(collector.shouldStop)
        case = _test_cases.TestCase('test_method')

        collector.startTest(case)

        # When
        with self.failure_exc_info() as exc_info:
            collector.addFailure(case, exc_info)

        # Then
        self.assertTrue(collector.shouldStop)

    def test_failfast_enabled_on_unexpected_success(self):
        # Given
        collector = ResultCollecter(failfast=False)
        self.assertFalse(collector.shouldStop)
        case = _test_cases.TestCase('test_method')

        collector.startTest(case)

        # When
        collector.addUnexpectedSuccess(case)

        # Then
        self.assertFalse(collector.shouldStop)

    def test_failfast_disabled_on_error(self):
        # Given
        collector = ResultCollecter(failfast=False)
        self.assertFalse(collector.shouldStop)
        case = _test_cases.TestCase('test_method')

        collector.startTest(case)

        # When
        with self.exc_info(RuntimeError) as exc_info:
            collector.addError(case, exc_info)

        # Then
        self.assertFalse(collector.shouldStop)

    def test_failfast_disabled_on_failure(self):
        # Given
        collector = ResultCollecter(failfast=False)
        self.assertFalse(collector.shouldStop)
        case = _test_cases.TestCase('test_method')

        collector.startTest(case)

        # When
        with self.failure_exc_info() as exc_info:
            collector.addFailure(case, exc_info)

        # Then
        self.assertFalse(collector.shouldStop)

    def test_failfast_disabled_on_unexpected_success(self):
        # Given
        collector = ResultCollecter(failfast=False)
        self.assertFalse(collector.shouldStop)
        case = _test_cases.TestCase('test_method')

        collector.startTest(case)

        # When
        collector.addUnexpectedSuccess(case)

        # Then
        self.assertFalse(collector.shouldStop)


class TestBuffering(ExcInfoFixture, unittest.TestCase):

    @patch('sys.stderr', new_callable=StringIO)
    def test_buffering_stderr(self, stderr):
        # Given
        handler = Mock(spec=IResultHandlerPlugin)
        collector = ResultCollecter(buffer=True)
        collector.add_result_handler(handler)
        test_stderr = 'My Test Output'
        start_time = datetime(2015, 12, 23, 8, 14, 12)
        duration = timedelta(seconds=10)
        end_time = start_time + duration
        expected_duration = TestDuration(start_time, end_time)
        case = _test_cases.TestCase('test_method')

        # When
        with patch('haas.result.datetime', new=MockDateTime(start_time)):
            collector.startTest(case)

        # Then
        self.assertTrue(handler.start_test.called)
        handler.start_test.reset_mock()

        # When
        sys.stderr.write(test_stderr)

        # Then
        self.assertEqual(stderr.getvalue(), '')

        # Given
        with self.exc_info(RuntimeError) as exc_info:
            expected_result = TestResult.from_test_case(
                case, TestCompletionStatus.error, expected_duration,
                exception=exc_info, stderr=test_stderr)
            # When
            with patch('haas.result.datetime', new=MockDateTime(end_time)):
                collector.addError(case, exc_info)
        collector.stopTest(case)

        # Then
        self.assertIn(test_stderr, expected_result.exception)
        handler.assert_called_once_with(expected_result)

    @patch('sys.stdout', new_callable=StringIO)
    def test_buffering_stdout(self, stdout):
        # Given
        handler = Mock(spec=IResultHandlerPlugin)
        collector = ResultCollecter(buffer=True)
        collector.add_result_handler(handler)
        test_stdout = 'My Test Output'
        start_time = datetime(2015, 12, 23, 8, 14, 12)
        duration = timedelta(seconds=10)
        end_time = start_time + duration
        expected_duration = TestDuration(start_time, end_time)
        case = _test_cases.TestCase('test_method')

        # When
        with patch('haas.result.datetime', new=MockDateTime(start_time)):
            collector.startTest(case)

        # Then
        self.assertTrue(handler.start_test.called)
        handler.start_test.reset_mock()

        # When
        sys.stdout.write(test_stdout)

        # Then
        self.assertEqual(stdout.getvalue(), '')

        # Given
        with self.exc_info(RuntimeError) as exc_info:
            expected_result = TestResult.from_test_case(
                case, TestCompletionStatus.error, expected_duration,
                exception=exc_info, stdout=test_stdout)

            # When
            with patch('haas.result.datetime', new=MockDateTime(end_time)):
                collector.addError(case, exc_info)
        collector.stopTest(case)

        # Then
        self.assertIn(test_stdout, expected_result.exception)
        handler.assert_called_once_with(expected_result)


class TestQuietResultHandler(ExcInfoFixture, unittest.TestCase):

    @patch('sys.stderr', new_callable=StringIO)
    def test_no_output_start_test_run(self, stderr):
        # Given
        handler = QuietTestResultHandler(test_count=1)

        # When
        handler.start_test_run()

        # Then
        output = stderr.getvalue()
        self.assertEqual(output, '')

    @patch('sys.stderr', new_callable=StringIO)
    def test_output_stop_test_run(self, stderr):
        # Given
        handler = QuietTestResultHandler(test_count=1)
        handler.start_test_run()

        # When
        handler.stop_test_run()

        # Then
        output = stderr.getvalue()
        self.assertTrue(output.startswith('\n' + handler.separator2))
        self.assertTrue(output.endswith('OK\n'))
        self.assertRegexpMatches(
            output.replace('\n', ''), r'--+.*?Ran 0 tests.*?OK')

    @patch('sys.stderr', new_callable=StringIO)
    def test_no_output_start_test(self, stderr):
        # Given
        handler = QuietTestResultHandler(test_count=1)
        case = _test_cases.TestCase('test_method')

        # When
        handler.start_test(case)

        # Then
        output = stderr.getvalue()
        self.assertEqual(output, '')

    @patch('sys.stderr', new_callable=StringIO)
    def test_no_output_stop_test(self, stderr):
        # Given
        handler = QuietTestResultHandler(test_count=1)
        case = _test_cases.TestCase('test_method')

        # When
        handler.stop_test(case)

        # Then
        output = stderr.getvalue()
        self.assertEqual(output, '')

    @patch('sys.stderr', new_callable=StringIO)
    def test_no_output_on_error(self, stderr):
        # Given
        start_time = datetime(2015, 12, 23, 8, 14, 12)
        duration = timedelta(seconds=10)
        end_time = start_time + duration
        expected_duration = TestDuration(start_time, end_time)
        case = _test_cases.TestCase('test_method')

        handler = QuietTestResultHandler(test_count=1)
        with self.exc_info(RuntimeError) as exc_info:
            result = TestResult.from_test_case(
                case, TestCompletionStatus.error, expected_duration,
                exception=exc_info)

        # When
        handler(result)

        # Then
        output = stderr.getvalue()
        self.assertEqual(output, '')

    @patch('sys.stderr', new_callable=StringIO)
    def test_no_output_on_failure(self, stderr):
        # Given
        start_time = datetime(2015, 12, 23, 8, 14, 12)
        duration = timedelta(seconds=10)
        end_time = start_time + duration
        expected_duration = TestDuration(start_time, end_time)
        case = _test_cases.TestCase('test_method')

        handler = QuietTestResultHandler(test_count=1)
        with self.failure_exc_info() as exc_info:
            result = TestResult.from_test_case(
                case, TestCompletionStatus.failure, expected_duration,
                exception=exc_info)

        # When
        handler(result)

        # Then
        output = stderr.getvalue()
        self.assertEqual(output, '')

    @patch('sys.stderr', new_callable=StringIO)
    def test_no_output_on_success(self, stderr):
        # Given
        start_time = datetime(2015, 12, 23, 8, 14, 12)
        duration = timedelta(seconds=10)
        end_time = start_time + duration
        expected_duration = TestDuration(start_time, end_time)
        case = _test_cases.TestCase('test_method')

        handler = QuietTestResultHandler(test_count=1)
        result = TestResult.from_test_case(
            case, TestCompletionStatus.success, expected_duration)

        # When
        handler(result)

        # Then
        output = stderr.getvalue()
        self.assertEqual(output, '')

    @patch('sys.stderr', new_callable=StringIO)
    def test_no_output_on_skip(self, stderr):
        # Given
        start_time = datetime(2015, 12, 23, 8, 14, 12)
        duration = timedelta(seconds=10)
        end_time = start_time + duration
        expected_duration = TestDuration(start_time, end_time)
        case = _test_cases.TestCase('test_method')

        handler = QuietTestResultHandler(test_count=1)
        result = TestResult.from_test_case(
            case, TestCompletionStatus.skipped, expected_duration,
            message='reason')

        # When
        handler(result)

        # Then
        output = stderr.getvalue()
        self.assertEqual(output, '')

    @patch('sys.stderr', new_callable=StringIO)
    def test_no_output_on_expected_fail(self, stderr):
        # Given
        start_time = datetime(2015, 12, 23, 8, 14, 12)
        duration = timedelta(seconds=10)
        end_time = start_time + duration
        expected_duration = TestDuration(start_time, end_time)
        case = _test_cases.TestCase('test_method')

        handler = QuietTestResultHandler(test_count=1)
        with self.exc_info(RuntimeError) as exc_info:
            result = TestResult.from_test_case(
                case, TestCompletionStatus.expected_failure, expected_duration,
                exception=exc_info)

        # When
        handler(result)

        # Then
        output = stderr.getvalue()
        self.assertEqual(output, '')

    @patch('sys.stderr', new_callable=StringIO)
    def test_no_output_on_unexpected_success(self, stderr):
        # Given
        start_time = datetime(2015, 12, 23, 8, 14, 12)
        duration = timedelta(seconds=10)
        end_time = start_time + duration
        expected_duration = TestDuration(start_time, end_time)
        case = _test_cases.TestCase('test_method')

        handler = QuietTestResultHandler(test_count=1)
        result = TestResult.from_test_case(
            case, TestCompletionStatus.unexpected_success, expected_duration)

        # When
        handler(result)

        # Then
        output = stderr.getvalue()
        self.assertEqual(output, '')

    @patch('sys.stderr', new_callable=StringIO)
    def test_no_output_with_error_on_stop_test_run(self, stderr):
        # Given
        start_time = datetime(2015, 12, 23, 8, 14, 12)
        duration = timedelta(seconds=10)
        end_time = start_time + duration
        expected_duration = TestDuration(start_time, end_time)
        case = _test_cases.TestCase('test_method')

        handler = QuietTestResultHandler(test_count=1)
        handler.start_test_run()
        with self.exc_info(RuntimeError) as exc_info:
            result = TestResult.from_test_case(
                case, TestCompletionStatus.error, expected_duration,
                exception=exc_info)

        # When
        handler(result)
        handler.stop_test_run()

        # Then
        output = stderr.getvalue().replace('\n', '')
        description = handler.get_test_description(
            case,).replace('(', r'\(').replace(')', r'\)')
        self.assertRegexpMatches(
            output, '{0}.*?Traceback.*?RuntimeError'.format(
                description))

    @patch('sys.stderr', new_callable=StringIO)
    def test_no_output_with_failure_on_stop_test_run(self, stderr):
        # Given
        start_time = datetime(2015, 12, 23, 8, 14, 12)
        duration = timedelta(seconds=10)
        end_time = start_time + duration
        expected_duration = TestDuration(start_time, end_time)
        case = _test_cases.TestCase('test_method')

        handler = QuietTestResultHandler(test_count=1)
        handler.start_test_run()
        with self.failure_exc_info() as exc_info:
            result = TestResult.from_test_case(
                case, TestCompletionStatus.failure, expected_duration,
                exception=exc_info)

        # When
        handler(result)
        handler.stop_test_run()

        # Then
        output = stderr.getvalue().replace('\n', '')
        description = handler.get_test_description(
            case,).replace('(', r'\(').replace(')', r'\)').replace('\n', '')
        self.assertRegexpMatches(
            output, '{0}.*?Traceback.*?AssertionError'.format(
                description))
        # The contents of unittest.TestCase should not be in the traceback
        self.assertNotIn('raise', output)


class TestStandardResultHandler(ExcInfoFixture, unittest.TestCase):

    @patch('sys.stderr', new_callable=StringIO)
    def test_no_output_start_test_run(self, stderr):
        # Given
        handler = StandardTestResultHandler(test_count=1)

        # When
        handler.start_test_run()

        # Then
        output = stderr.getvalue()
        self.assertEqual(output, '')

    @patch('sys.stderr', new_callable=StringIO)
    def test_output_stop_test_run(self, stderr):
        # Given
        handler = StandardTestResultHandler(test_count=1)
        handler.start_test_run()

        # When
        handler.stop_test_run()

        # Then
        output = stderr.getvalue()
        self.assertTrue(output.startswith('\n' + handler.separator2))
        self.assertTrue(output.endswith('OK\n'))
        self.assertRegexpMatches(
            output.replace('\n', ''), r'--+.*?Ran 0 tests.*?OK')

    @patch('sys.stderr', new_callable=StringIO)
    def test_no_output_start_test(self, stderr):
        # Given
        handler = StandardTestResultHandler(test_count=1)
        case = _test_cases.TestCase('test_method')

        # When
        handler.start_test(case)

        # Then
        output = stderr.getvalue()
        self.assertEqual(output, '')

    @patch('sys.stderr', new_callable=StringIO)
    def test_no_output_stop_test(self, stderr):
        # Given
        handler = StandardTestResultHandler(test_count=1)
        case = _test_cases.TestCase('test_method')

        # When
        handler.stop_test(case)

        # Then
        output = stderr.getvalue()
        self.assertEqual(output, '')

    @patch('sys.stderr', new_callable=StringIO)
    def test_no_output_on_error(self, stderr):
        # Given
        start_time = datetime(2015, 12, 23, 8, 14, 12)
        duration = timedelta(seconds=10)
        end_time = start_time + duration
        expected_duration = TestDuration(start_time, end_time)
        case = _test_cases.TestCase('test_method')

        handler = StandardTestResultHandler(test_count=1)
        with self.exc_info(RuntimeError) as exc_info:
            result = TestResult.from_test_case(
                case, TestCompletionStatus.error, expected_duration,
                exception=exc_info)

        # When
        handler(result)

        # Then
        output = stderr.getvalue()
        self.assertEqual(output, 'E')

    @patch('sys.stderr', new_callable=StringIO)
    def test_no_output_on_failure(self, stderr):
        # Given
        start_time = datetime(2015, 12, 23, 8, 14, 12)
        duration = timedelta(seconds=10)
        end_time = start_time + duration
        expected_duration = TestDuration(start_time, end_time)
        case = _test_cases.TestCase('test_method')

        handler = StandardTestResultHandler(test_count=1)
        with self.failure_exc_info() as exc_info:
            result = TestResult.from_test_case(
                case, TestCompletionStatus.failure, expected_duration,
                exception=exc_info)

        # When
        handler(result)

        # Then
        output = stderr.getvalue()
        self.assertEqual(output, 'F')

    @patch('sys.stderr', new_callable=StringIO)
    def test_no_output_on_success(self, stderr):
        # Given
        start_time = datetime(2015, 12, 23, 8, 14, 12)
        duration = timedelta(seconds=10)
        end_time = start_time + duration
        expected_duration = TestDuration(start_time, end_time)
        case = _test_cases.TestCase('test_method')

        handler = StandardTestResultHandler(test_count=1)
        result = TestResult.from_test_case(
            case, TestCompletionStatus.success, expected_duration)

        # When
        handler(result)

        # Then
        output = stderr.getvalue()
        self.assertEqual(output, '.')

    @patch('sys.stderr', new_callable=StringIO)
    def test_no_output_on_skip(self, stderr):
        # Given
        start_time = datetime(2015, 12, 23, 8, 14, 12)
        duration = timedelta(seconds=10)
        end_time = start_time + duration
        expected_duration = TestDuration(start_time, end_time)
        case = _test_cases.TestCase('test_method')

        handler = StandardTestResultHandler(test_count=1)
        result = TestResult.from_test_case(
            case, TestCompletionStatus.skipped, expected_duration,
            message='reason')

        # When
        handler(result)

        # Then
        output = stderr.getvalue()
        self.assertEqual(output, 's')

    @patch('sys.stderr', new_callable=StringIO)
    def test_no_output_on_expected_fail(self, stderr):
        # Given
        start_time = datetime(2015, 12, 23, 8, 14, 12)
        duration = timedelta(seconds=10)
        end_time = start_time + duration
        expected_duration = TestDuration(start_time, end_time)
        case = _test_cases.TestCase('test_method')

        handler = StandardTestResultHandler(test_count=1)
        with self.exc_info(RuntimeError) as exc_info:
            result = TestResult.from_test_case(
                case, TestCompletionStatus.expected_failure, expected_duration,
                exception=exc_info)

        # When
        handler(result)

        # Then
        output = stderr.getvalue()
        self.assertEqual(output, 'x')

    @patch('sys.stderr', new_callable=StringIO)
    def test_no_output_on_unexpected_success(self, stderr):
        # Given
        start_time = datetime(2015, 12, 23, 8, 14, 12)
        duration = timedelta(seconds=10)
        end_time = start_time + duration
        expected_duration = TestDuration(start_time, end_time)
        case = _test_cases.TestCase('test_method')

        handler = StandardTestResultHandler(test_count=1)
        result = TestResult.from_test_case(
            case, TestCompletionStatus.unexpected_success, expected_duration)

        # When
        handler(result)

        # Then
        output = stderr.getvalue()
        self.assertEqual(output, 'u')

    @patch('sys.stderr', new_callable=StringIO)
    def test_no_output_with_error_on_stop_test_run(self, stderr):
        # Given
        start_time = datetime(2015, 12, 23, 8, 14, 12)
        duration = timedelta(seconds=10)
        end_time = start_time + duration
        expected_duration = TestDuration(start_time, end_time)
        case = _test_cases.TestCase('test_method')

        handler = StandardTestResultHandler(test_count=1)
        handler.start_test_run()
        with self.exc_info(RuntimeError) as exc_info:
            result = TestResult.from_test_case(
                case, TestCompletionStatus.error, expected_duration,
                exception=exc_info)

        # When
        handler(result)
        handler.stop_test_run()

        # Then
        output = stderr.getvalue().replace('\n', '')
        description = handler.get_test_description(
            case).replace('(', r'\(').replace(')', r'\)')
        self.assertRegexpMatches(
            output, '{0}.*?Traceback.*?RuntimeError'.format(
                description))

    @patch('sys.stderr', new_callable=StringIO)
    def test_no_output_with_failure_on_stop_test_run(self, stderr):
        # Given
        start_time = datetime(2015, 12, 23, 8, 14, 12)
        duration = timedelta(seconds=10)
        end_time = start_time + duration
        expected_duration = TestDuration(start_time, end_time)
        case = _test_cases.TestCase('test_method')

        handler = StandardTestResultHandler(test_count=1)
        handler.start_test_run()
        with self.failure_exc_info() as exc_info:
            result = TestResult.from_test_case(
                case, TestCompletionStatus.failure, expected_duration,
                exception=exc_info)

        # When
        handler(result)
        handler.stop_test_run()

        # Then
        output = stderr.getvalue().replace('\n', '')
        description = handler.get_test_description(
            case).replace('(', r'\(').replace(')', r'\)').replace('\n', '')
        self.assertRegexpMatches(
            output, '{0}.*?Traceback.*?AssertionError'.format(
                description))
        # The contents of unittest.TestCase should not be in the traceback
        self.assertNotIn('raise', output)


class TestVerboseResultHandler(ExcInfoFixture, unittest.TestCase):

    @patch('sys.stderr', new_callable=StringIO)
    def test_output_start_test_run(self, stderr):
        # Given
        handler = VerboseTestResultHandler(test_count=1)

        # When
        handler.start_test_run()

        # Then
        output = stderr.getvalue()
        self.assertEqual(output, '')

    @patch('sys.stderr', new_callable=StringIO)
    def test_no_output_stop_test_run(self, stderr):
        # Given
        handler = VerboseTestResultHandler(test_count=1)
        handler.start_test_run()

        # When
        handler.stop_test_run()

        # Then
        output = stderr.getvalue()
        self.assertTrue(output.startswith('\n' + handler.separator2))
        self.assertTrue(output.endswith('OK\n'))
        self.assertRegexpMatches(
            output.replace('\n', ''), r'--+.*?Ran 0 tests.*?OK')

    @patch('time.ctime')
    @patch('sys.stderr', new_callable=StringIO)
    def test_output_start_test(self, stderr, mock_ctime):
        # Given
        case = _test_cases.TestCase('test_method')
        handler = VerboseTestResultHandler(test_count=1)
        mock_ctime.return_value = expected_time = ctime()
        expected_description = handler.get_test_description(case)

        # When
        handler.start_test(case)

        # Then
        output = stderr.getvalue()
        self.assertEqual(
            output, '[{0}] (1/1) {1} ... '.format(
                expected_time, expected_description))

    @patch('sys.stderr', new_callable=StringIO)
    def test_no_output_stop_test(self, stderr):
        # Given
        handler = VerboseTestResultHandler(test_count=1)
        case = _test_cases.TestCase('test_method')

        # When
        handler.stop_test(case)

        # Then
        output = stderr.getvalue()
        self.assertEqual(output, '')

    @patch('sys.stderr', new_callable=StringIO)
    def test_output_on_error(self, stderr):
        # Given
        start_time = datetime(2015, 12, 23, 8, 14, 12)
        duration = timedelta(seconds=10)
        end_time = start_time + duration
        expected_duration = TestDuration(start_time, end_time)
        case = _test_cases.TestCase('test_method')

        handler = VerboseTestResultHandler(test_count=1)
        with self.exc_info(RuntimeError) as exc_info:
            result = TestResult.from_test_case(
                case, TestCompletionStatus.error, expected_duration,
                exception=exc_info)

        # When
        handler(result)

        # Then
        output = stderr.getvalue()
        self.assertEqual(output, 'ERROR\n')

    @patch('sys.stderr', new_callable=StringIO)
    def test_output_on_failure(self, stderr):
        # Given
        start_time = datetime(2015, 12, 23, 8, 14, 12)
        duration = timedelta(seconds=10)
        end_time = start_time + duration
        expected_duration = TestDuration(start_time, end_time)
        case = _test_cases.TestCase('test_method')

        handler = VerboseTestResultHandler(test_count=1)
        with self.failure_exc_info() as exc_info:
            result = TestResult.from_test_case(
                case, TestCompletionStatus.failure, expected_duration,
                exception=exc_info)

        # When
        handler(result)

        # Then
        output = stderr.getvalue()
        self.assertEqual(output, 'FAIL\n')

    @patch('sys.stderr', new_callable=StringIO)
    def test_output_on_success(self, stderr):
        # Given
        start_time = datetime(2015, 12, 23, 8, 14, 12)
        duration = timedelta(seconds=10)
        end_time = start_time + duration
        expected_duration = TestDuration(start_time, end_time)
        case = _test_cases.TestCase('test_method')

        handler = VerboseTestResultHandler(test_count=1)
        result = TestResult.from_test_case(
            case, TestCompletionStatus.success, expected_duration)

        # When
        handler(result)

        # Then
        output = stderr.getvalue()
        self.assertEqual(output, 'ok\n')

    @patch('sys.stderr', new_callable=StringIO)
    def test_output_on_skip(self, stderr):
        # Given
        start_time = datetime(2015, 12, 23, 8, 14, 12)
        duration = timedelta(seconds=10)
        end_time = start_time + duration
        expected_duration = TestDuration(start_time, end_time)
        case = _test_cases.TestCase('test_method')

        handler = VerboseTestResultHandler(test_count=1)
        result = TestResult.from_test_case(
            case, TestCompletionStatus.skipped, expected_duration,
            message='reason')

        # When
        handler(result)

        # Then
        output = stderr.getvalue()
        self.assertEqual(output, 'skipped \'reason\'\n')

    @patch('sys.stderr', new_callable=StringIO)
    def test_output_on_expected_fail(self, stderr):
        # Given
        start_time = datetime(2015, 12, 23, 8, 14, 12)
        duration = timedelta(seconds=10)
        end_time = start_time + duration
        expected_duration = TestDuration(start_time, end_time)
        case = _test_cases.TestCase('test_method')

        handler = VerboseTestResultHandler(test_count=1)
        with self.exc_info(RuntimeError) as exc_info:
            result = TestResult.from_test_case(
                case, TestCompletionStatus.expected_failure, expected_duration,
                exception=exc_info)

        # When
        handler(result)

        # Then
        output = stderr.getvalue()
        self.assertEqual(output, 'expected failure\n')

    @patch('sys.stderr', new_callable=StringIO)
    def test_output_on_unexpected_success(self, stderr):
        # Given
        start_time = datetime(2015, 12, 23, 8, 14, 12)
        duration = timedelta(seconds=10)
        end_time = start_time + duration
        expected_duration = TestDuration(start_time, end_time)
        case = _test_cases.TestCase('test_method')

        handler = VerboseTestResultHandler(test_count=1)
        result = TestResult.from_test_case(
            case, TestCompletionStatus.unexpected_success, expected_duration)

        # When
        handler(result)

        # Then
        output = stderr.getvalue()
        self.assertEqual(output, 'unexpected success\n')

    @patch('sys.stderr', new_callable=StringIO)
    def test_output_with_error_on_stop_test_run(self, stderr):
        # Given
        start_time = datetime(2015, 12, 23, 8, 14, 12)
        duration = timedelta(seconds=10)
        end_time = start_time + duration
        expected_duration = TestDuration(start_time, end_time)
        case = _test_cases.TestCase('test_method')

        handler = VerboseTestResultHandler(test_count=1)
        handler.start_test_run()
        with self.exc_info(RuntimeError) as exc_info:
            result = TestResult.from_test_case(
                case, TestCompletionStatus.error, expected_duration,
                exception=exc_info)

        # When
        handler(result)
        handler.stop_test_run()

        # Then
        output = stderr.getvalue().replace('\n', '')
        description = handler.get_test_description(
            case).replace('(', r'\(').replace(')', r'\)')
        self.assertRegexpMatches(
            output, '{0}.*?Traceback.*?RuntimeError'.format(
                description))

    @patch('sys.stderr', new_callable=StringIO)
    def test_output_with_failure_on_stop_test_run(self, stderr):
        # Given
        start_time = datetime(2015, 12, 23, 8, 14, 12)
        duration = timedelta(seconds=10)
        end_time = start_time + duration
        expected_duration = TestDuration(start_time, end_time)
        case = _test_cases.TestCase('test_method')

        handler = VerboseTestResultHandler(test_count=1)
        handler.start_test_run()
        with self.failure_exc_info() as exc_info:
            result = TestResult.from_test_case(
                case, TestCompletionStatus.failure, expected_duration,
                exception=exc_info)

        # When
        handler(result)
        handler.stop_test_run()

        # Then
        output = stderr.getvalue().replace('\n', '')
        description = handler.get_test_description(
            case).replace('(', r'\(').replace(')', r'\)').replace('\n', '')
        self.assertRegexpMatches(
            output, '{0}.*?Traceback.*?AssertionError'.format(
                description))
        # The contents of unittest.TestCase should not be in the traceback
        self.assertNotIn('raise', output)
