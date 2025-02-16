import pytest
import unittest
from unittest.mock import patch, Mock, mock_open
from pynonymizer.cli import cli
from pynonymizer.pynonymize import (
    ArgumentValidationError,
    DatabaseConnectionError,
    pynonymize,
)
from types import SimpleNamespace


def test_pynonymize_missing_db_credentials():
    with pytest.raises(ArgumentValidationError):
        pynonymize(
            input_path="input.sql",
            strategyfile_path="strategyfile.yml",
            output_path="output.sql",
            db_user=None,
            db_password=None,
        )


@patch("dotenv.find_dotenv", Mock())
@patch("dotenv.load_dotenv", Mock())
@patch("pynonymizer.pynonymize.read_config")
@patch("pynonymizer.pynonymize.get_provider")
@patch("pynonymizer.pynonymize.FakeColumnGenerator")
@patch("pynonymizer.pynonymize.StrategyParser")
@patch("builtins.open", mock_open(read_data="TESTFILEDATA"))
class MainProcessTests(unittest.TestCase):
    def test_any_db_kwarg(
        self, StrategyParser, FakeColumnSet, get_provider, read_config
    ):
        """
        test that dynamic args are passed to the provider properly e.g. mssql_blah
        """
        pynonymize(
            input_path="TEST_INPUT",
            strategyfile_path="TEST_STRATEGYFILE",
            output_path="TEST_OUTPUT",
            db_type="mssql",
            db_host="TEST_HOST",
            db_port="TEST_PORT",
            db_name="TEST_NAME",
            db_user="TEST_USER",
            db_password="TEST_PASSWORD",
            fake_locale="TEST_LOCALE",
            mysql_other_amazing_var="TEST_DYNAMIC_VAR",  # as this is mssql, this should be ignored
            mssql_special_provider_var="TEST_DYNAMIC_VAR2",
        )
        StrategyParser.return_value.parse_config.assert_called()
        get_provider.assert_called_with(
            type="mssql",
            db_host="TEST_HOST",
            db_port="TEST_PORT",
            db_user="TEST_USER",
            db_pass="TEST_PASSWORD",
            db_name="TEST_NAME",
            seed_rows=150,
            special_provider_var="TEST_DYNAMIC_VAR2",
        )

    def test_pynonymize_main_process(
        self, StrategyParser, FakeColumnSet, get_provider, read_config
    ):
        """
        a rough smoke test for the cli process. This needs an integration test to back it up.
        """
        pynonymize(
            input_path="TEST_INPUT",
            strategyfile_path="TEST_STRATEGYFILE",
            output_path="TEST_OUTPUT",
            db_type="TEST_TYPE",
            db_host="TEST_HOST",
            db_port="TEST_PORT",
            db_name="TEST_NAME",
            db_user="TEST_USER",
            db_password="TEST_PASSWORD",
            fake_locale="TEST_LOCALE",
            seed_rows=999,
        )
        StrategyParser.return_value.parse_config.assert_called()
        get_provider.assert_called_with(
            type="TEST_TYPE",
            db_host="TEST_HOST",
            db_port="TEST_PORT",
            db_user="TEST_USER",
            db_pass="TEST_PASSWORD",
            db_name="TEST_NAME",
            seed_rows=999,
        )

        provider = get_provider.return_value
        provider.create_database.assert_called()
        provider.restore_database.assert_called()
        provider.anonymize_database.assert_called()
        provider.dump_database.assert_called()
        provider.drop_database.assert_called()

    def test_pynonymize_only_step(
        self, StrategyParser, FakeColumnSet, get_provider, read_config
    ):
        pynonymize(
            input_path="TEST_INPUT",
            strategyfile_path="TEST_STRATEGYFILE",
            output_path="TEST_OUTPUT",
            db_type="TEST_TYPE",
            db_host="TEST_HOST",
            db_port="TEST_PORT",
            db_name="TEST_NAME",
            db_user="TEST_USER",
            db_password="TEST_PASSWORD",
            fake_locale="TEST_LOCALE",
            only_step="ANONYMIZE_DB",
        )
        StrategyParser.return_value.parse_config.assert_called()
        get_provider.assert_called_with(
            type="TEST_TYPE",
            db_host="TEST_HOST",
            db_port="TEST_PORT",
            db_user="TEST_USER",
            db_pass="TEST_PASSWORD",
            db_name="TEST_NAME",
            seed_rows=150,
        )

        provider = get_provider.return_value
        provider.create_database.assert_not_called()
        provider.restore_database.assert_not_called()
        provider.anonymize_database.assert_called()
        provider.dump_database.assert_not_called()
        provider.drop_database.assert_not_called()

    def test_pynonymize_stop_at_step(
        self, StrategyParser, FakeColumnSet, get_provider, read_config
    ):
        pynonymize(
            input_path="TEST_INPUT",
            strategyfile_path="TEST_STRATEGYFILE",
            output_path="TEST_OUTPUT",
            db_type="TEST_TYPE",
            db_host="TEST_HOST",
            db_port="TEST_PORT",
            db_name="TEST_NAME",
            db_user="TEST_USER",
            db_password="TEST_PASSWORD",
            fake_locale="TEST_LOCALE",
            stop_at_step="ANONYMIZE_DB",
        )
        StrategyParser.return_value.parse_config.assert_called()
        get_provider.assert_called_with(
            type="TEST_TYPE",
            db_host="TEST_HOST",
            db_port="TEST_PORT",
            db_user="TEST_USER",
            db_pass="TEST_PASSWORD",
            db_name="TEST_NAME",
            seed_rows=150,
        )

        provider = get_provider.return_value
        provider.create_database.assert_called()
        provider.restore_database.assert_called()
        provider.anonymize_database.assert_called()
        provider.dump_database.assert_not_called()
        provider.drop_database.assert_not_called()

    def test_pynonymize_skip_steps(
        self, StrategyParser, FakeColumnSet, get_provider, read_config
    ):
        pynonymize(
            input_path="TEST_INPUT",
            strategyfile_path="TEST_STRATEGYFILE",
            output_path="TEST_OUTPUT",
            db_type="TEST_TYPE",
            db_host="TEST_HOST",
            db_port="TEST_PORT",
            db_name="TEST_NAME",
            db_user="TEST_USER",
            db_password="TEST_PASSWORD",
            fake_locale="TEST_LOCALE",
            skip_steps=["ANONYMIZE_DB", "CREATE_DB", "DUMP_DB"],
        )
        get_provider.assert_called_with(
            type="TEST_TYPE",
            db_host="TEST_HOST",
            db_port="TEST_PORT",
            db_user="TEST_USER",
            db_pass="TEST_PASSWORD",
            db_name="TEST_NAME",
            seed_rows=150,
        )

        provider = get_provider.return_value
        provider.create_database.assert_not_called()
        provider.restore_database.assert_called()
        provider.anonymize_database.assert_not_called()
        provider.dump_database.assert_not_called()
        provider.drop_database.assert_called()

    def test_pynonymize_start_at_step(
        self, StrategyParser, FakeColumnSet, get_provider, read_config
    ):
        pynonymize(
            input_path="TEST_INPUT",
            strategyfile_path="TEST_STRATEGYFILE",
            output_path="TEST_OUTPUT",
            db_type="TEST_TYPE",
            db_host="TEST_HOST",
            db_port="TEST_PORT",
            db_name="TEST_NAME",
            db_user="TEST_USER",
            db_password="TEST_PASSWORD",
            fake_locale="TEST_LOCALE",
            start_at_step="ANONYMIZE_DB",
        )
        StrategyParser.return_value.parse_config.assert_called()
        get_provider.assert_called_with(
            type="TEST_TYPE",
            db_host="TEST_HOST",
            db_port="TEST_PORT",
            db_user="TEST_USER",
            db_pass="TEST_PASSWORD",
            db_name="TEST_NAME",
            seed_rows=150,
        )

        provider = get_provider.return_value
        provider.create_database.assert_not_called()
        provider.restore_database.assert_not_called()
        provider.anonymize_database.assert_called()
        provider.dump_database.assert_called()
        provider.drop_database.assert_called()


@patch("dotenv.find_dotenv", Mock())
@patch("dotenv.load_dotenv", Mock())
@patch("pynonymizer.pynonymize.read_config")
@patch("pynonymizer.pynonymize.get_provider")
@patch("pynonymizer.pynonymize.FakeColumnGenerator")
@patch("pynonymizer.pynonymize.StrategyParser")
@patch("builtins.open", mock_open(read_data="TESTFILEDATA"))
class OptionalArgumentsSkippedTests(unittest.TestCase):
    """
    pynonymize should not throw argument validation errors for missing "mandatory" args
    that are only mandatory for certain steps.

    START = 0
    GET_SOURCE = 100
    CREATE_DB = 200
    RESTORE_DB = 300
    ANONYMIZE_DB = 400
    DUMP_DB = 500
    DROP_DB = 600
    END = 9999

    """

    def test_optional_input_when_skip_input_steps(
        self, StrategyParser, FakeColumnSet, get_provider, read_config
    ):
        pynonymize(
            input_path=None,
            strategyfile_path="TEST_STRATEGYFILE",
            output_path="TEST_OUTPUT",
            db_type="TEST_TYPE",
            db_host="TEST_HOST",
            db_port="TEST_PORT",
            db_name="TEST_NAME",
            db_user="TEST_USER",
            db_password="TEST_PASSWORD",
            fake_locale="TEST_LOCALE",
            start_at_step=None,
            stop_at_step=None,
            skip_steps=["RESTORE_DB"],
        )

        StrategyParser.return_value.parse_config.assert_called()
        get_provider.assert_called_with(
            type="TEST_TYPE",
            db_host="TEST_HOST",
            db_port="TEST_PORT",
            db_user="TEST_USER",
            db_pass="TEST_PASSWORD",
            db_name="TEST_NAME",
            seed_rows=150,
        )

        provider = get_provider.return_value
        provider.create_database.assert_called()
        provider.restore_database.assert_not_called()
        provider.anonymize_database.assert_called()
        provider.dump_database.assert_called()
        provider.drop_database.assert_called()

    def test_optional_input_when_start_at_after_input_steps(
        self, StrategyParser, FakeColumnSet, get_provider, read_config
    ):
        pynonymize(
            input_path=None,
            strategyfile_path="TEST_STRATEGYFILE",
            output_path="TEST_OUTPUT",
            db_type="TEST_TYPE",
            db_host="TEST_HOST",
            db_port="TEST_PORT",
            db_name="TEST_NAME",
            db_user="TEST_USER",
            db_password="TEST_PASSWORD",
            fake_locale="TEST_LOCALE",
            start_at_step="ANONYMIZE_DB",
            stop_at_step=None,
            skip_steps=None,
        )

        StrategyParser.return_value.parse_config.assert_called()
        get_provider.assert_called_with(
            type="TEST_TYPE",
            db_host="TEST_HOST",
            db_port="TEST_PORT",
            db_user="TEST_USER",
            db_pass="TEST_PASSWORD",
            db_name="TEST_NAME",
            seed_rows=150,
        )

        provider = get_provider.return_value
        provider.create_database.assert_not_called()
        provider.restore_database.assert_not_called()
        provider.anonymize_database.assert_called()
        provider.dump_database.assert_called()
        provider.drop_database.assert_called()

    def test_optional_input_when_stop_at_before_input_steps(
        self, StrategyParser, FakeColumnSet, get_provider, read_config
    ):
        pynonymize(
            input_path=None,
            strategyfile_path="TEST_STRATEGYFILE",
            output_path="TEST_OUTPUT",
            db_type="TEST_TYPE",
            db_host="TEST_HOST",
            db_port="TEST_PORT",
            db_name="TEST_NAME",
            db_user="TEST_USER",
            db_password="TEST_PASSWORD",
            fake_locale="TEST_LOCALE",
            start_at_step=None,
            stop_at_step="CREATE_DB",
            skip_steps=None,
        )

        get_provider.assert_called_with(
            type="TEST_TYPE",
            db_host="TEST_HOST",
            db_port="TEST_PORT",
            db_user="TEST_USER",
            db_pass="TEST_PASSWORD",
            db_name="TEST_NAME",
            seed_rows=150,
        )

        provider = get_provider.return_value
        provider.create_database.assert_called()
        provider.restore_database.assert_not_called()
        provider.anonymize_database.assert_not_called()
        provider.dump_database.assert_not_called()
        provider.drop_database.assert_not_called()

    def test_optional_strategyfile_when_skip_anonymize(
        self, StrategyParser, FakeColumnSet, get_provider, read_config
    ):
        pynonymize(
            input_path="TEST_INPUT",
            strategyfile_path=None,
            output_path="TEST_OUTPUT",
            db_type="TEST_TYPE",
            db_host="TEST_HOST",
            db_port="TEST_PORT",
            db_name="TEST_NAME",
            db_user="TEST_USER",
            db_password="TEST_PASSWORD",
            fake_locale="TEST_LOCALE",
            start_at_step=None,
            stop_at_step=None,
            skip_steps=["ANONYMIZE_DB"],
        )
        get_provider.assert_called_with(
            type="TEST_TYPE",
            db_host="TEST_HOST",
            db_port="TEST_PORT",
            db_user="TEST_USER",
            db_pass="TEST_PASSWORD",
            db_name="TEST_NAME",
            seed_rows=150,
        )

        provider = get_provider.return_value
        provider.create_database.assert_called()
        provider.restore_database.assert_called()
        provider.anonymize_database.assert_not_called()
        provider.dump_database.assert_called()
        provider.drop_database.assert_called()

    def test_optional_strategyfile_when_start_at_after_anonymize(
        self, StrategyParser, FakeColumnSet, get_provider, read_config
    ):
        pynonymize(
            input_path="TEST_INPUT",
            strategyfile_path=None,
            output_path="TEST_OUTPUT",
            db_type="TEST_TYPE",
            db_host="TEST_HOST",
            db_port="TEST_PORT",
            db_name="TEST_NAME",
            db_user="TEST_USER",
            db_password="TEST_PASSWORD",
            fake_locale="TEST_LOCALE",
            start_at_step="DUMP_DB",
            stop_at_step=None,
            skip_steps=None,
        )
        get_provider.assert_called_with(
            type="TEST_TYPE",
            db_host="TEST_HOST",
            db_port="TEST_PORT",
            db_user="TEST_USER",
            db_pass="TEST_PASSWORD",
            db_name="TEST_NAME",
            seed_rows=150,
        )

        provider = get_provider.return_value
        provider.create_database.assert_not_called()
        provider.restore_database.assert_not_called()
        provider.anonymize_database.assert_not_called()
        provider.dump_database.assert_called()
        provider.drop_database.assert_called()

    def test_optional_strategyfile_when_stop_at_before_anonymize(
        self, StrategyParser, FakeColumnSet, get_provider, read_config
    ):
        pynonymize(
            input_path="TEST_INPUT",
            strategyfile_path=None,
            output_path="TEST_OUTPUT",
            db_type="TEST_TYPE",
            db_host="TEST_HOST",
            db_port="TEST_PORT",
            db_name="TEST_NAME",
            db_user="TEST_USER",
            db_password="TEST_PASSWORD",
            fake_locale="TEST_LOCALE",
            start_at_step=None,
            stop_at_step="RESTORE_DB",
            skip_steps=None,
        )
        get_provider.assert_called_with(
            type="TEST_TYPE",
            db_host="TEST_HOST",
            db_port="TEST_PORT",
            db_user="TEST_USER",
            db_pass="TEST_PASSWORD",
            db_name="TEST_NAME",
            seed_rows=150,
        )

        provider = get_provider.return_value
        provider.create_database.assert_called()
        provider.restore_database.assert_called()
        provider.anonymize_database.assert_not_called()
        provider.dump_database.assert_not_called()
        provider.drop_database.assert_not_called()

    def test_optional_output_when_skip_output_steps(
        self, StrategyParser, FakeColumnSet, get_provider, read_config
    ):
        pynonymize(
            input_path="TEST_INPUT",
            strategyfile_path="TEST_STRATEGYFILE",
            output_path=None,
            db_type="TEST_TYPE",
            db_host="TEST_HOST",
            db_port="TEST_PORT",
            db_name="TEST_NAME",
            db_user="TEST_USER",
            db_password="TEST_PASSWORD",
            fake_locale="TEST_LOCALE",
            start_at_step=None,
            stop_at_step=None,
            skip_steps=["DUMP_DB"],
        )

        StrategyParser.return_value.parse_config.assert_called()
        get_provider.assert_called_with(
            type="TEST_TYPE",
            db_host="TEST_HOST",
            db_port="TEST_PORT",
            db_user="TEST_USER",
            db_pass="TEST_PASSWORD",
            db_name="TEST_NAME",
            seed_rows=150,
        )

        provider = get_provider.return_value
        provider.create_database.assert_called()
        provider.restore_database.assert_called()
        provider.anonymize_database.assert_called()
        provider.dump_database.assert_not_called()
        provider.drop_database.assert_called()

    def test_optional_output_when_start_at_after_output_steps(
        self, StrategyParser, FakeColumnSet, get_provider, read_config
    ):
        pynonymize(
            input_path="TEST_INPUT",
            strategyfile_path="TEST_STRATEGYFILE",
            output_path=None,
            db_type="TEST_TYPE",
            db_host="TEST_HOST",
            db_port="TEST_PORT",
            db_name="TEST_NAME",
            db_user="TEST_USER",
            db_password="TEST_PASSWORD",
            fake_locale="TEST_LOCALE",
            start_at_step="DROP_DB",
            stop_at_step=None,
            skip_steps=None,
        )
        get_provider.assert_called_with(
            type="TEST_TYPE",
            db_host="TEST_HOST",
            db_port="TEST_PORT",
            db_user="TEST_USER",
            db_pass="TEST_PASSWORD",
            db_name="TEST_NAME",
            seed_rows=150,
        )

        provider = get_provider.return_value
        provider.create_database.assert_not_called()
        provider.restore_database.assert_not_called()
        provider.anonymize_database.assert_not_called()
        provider.dump_database.assert_not_called()
        provider.drop_database.assert_called()

    def test_optional_output_when_stop_at_before_output_steps(
        self, StrategyParser, FakeColumnSet, get_provider, read_config
    ):
        pynonymize(
            input_path="TEST_INPUT",
            strategyfile_path="TEST_STRATEGYFILE",
            output_path=None,
            db_type="TEST_TYPE",
            db_host="TEST_HOST",
            db_port="TEST_PORT",
            db_name="TEST_NAME",
            db_user="TEST_USER",
            db_password="TEST_PASSWORD",
            fake_locale="TEST_LOCALE",
            start_at_step=None,
            stop_at_step=None,
            skip_steps=["DUMP_DB"],
        )

        StrategyParser.return_value.parse_config.assert_called()
        get_provider.assert_called_with(
            type="TEST_TYPE",
            db_host="TEST_HOST",
            db_port="TEST_PORT",
            db_user="TEST_USER",
            db_pass="TEST_PASSWORD",
            db_name="TEST_NAME",
            seed_rows=150,
        )

        provider = get_provider.return_value
        provider.create_database.assert_called()
        provider.restore_database.assert_called()
        provider.anonymize_database.assert_called()
        provider.dump_database.assert_not_called()
        provider.drop_database.assert_called()
