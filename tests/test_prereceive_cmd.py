from unittest.mock import Mock, patch

from click.testing import CliRunner

from ggshield.cmd import cli
from ggshield.utils import EMPTY_SHA, EMPTY_TREE


class TestPreReceive:
    @patch("ggshield.pre_receive_cmd.get_list_commit_SHA")
    @patch("ggshield.pre_receive_cmd.scan_commit_range")
    @patch("ggshield.pre_receive_cmd.check_git_dir")
    def test_stdin_input(
        self,
        check_dir_mock: Mock,
        scan_commit_range_mock: Mock,
        get_list_mock: Mock,
        cli_fs_runner: CliRunner,
    ):
        """
        GIVEN 20 commits through stdin input
        WHEN the command is run
        THEN it should pass onto scan and return 0
        """
        scan_commit_range_mock.return_value = 0
        get_list_mock.return_value = ["a" for _ in range(20)]

        result = cli_fs_runner.invoke(
            cli, ["-v", "scan", "pre-receive"], input="bbbb\naaaa\norigin/main\n"
        )
        get_list_mock.assert_called_once_with("--max-count=51 bbbb" + "..." + "aaaa")
        scan_commit_range_mock.assert_called_once()
        assert "Commits to scan: 20" in result.output
        assert result.exit_code == 0

    @patch("ggshield.pre_receive_cmd.get_list_commit_SHA")
    @patch("ggshield.pre_receive_cmd.scan_commit_range")
    @patch("ggshield.pre_receive_cmd.check_git_dir")
    def test_stdin_input_secret(
        self,
        check_dir_mock: Mock,
        scan_commit_range_mock: Mock,
        get_list_mock: Mock,
        cli_fs_runner: CliRunner,
    ):
        """
        GIVEN 20 commits through stdin input
        WHEN the command is run and there are secrets
        THEN it should return a special remediation message
        """
        scan_commit_range_mock.return_value = 1
        get_list_mock.return_value = ["a" for _ in range(20)]

        result = cli_fs_runner.invoke(
            cli, ["-v", "scan", "pre-receive"], input="bbbb\naaaa\norigin/main\n"
        )
        get_list_mock.assert_called_once_with("--max-count=51 bbbb" + "..." + "aaaa")
        scan_commit_range_mock.assert_called_once()
        assert (
            "if those secrets are false positives and you still want your push to pass, run:\n'git push -o breakglass'"
            in result.output
        )
        assert result.exit_code == 1

    @patch("ggshield.pre_receive_cmd.get_list_commit_SHA")
    @patch("ggshield.pre_receive_cmd.scan_commit_range")
    @patch("ggshield.pre_receive_cmd.check_git_dir")
    def test_stdin_input_no_commits(
        self,
        check_dir_mock: Mock,
        scan_commit_range_mock: Mock,
        get_list_mock: Mock,
        cli_fs_runner: CliRunner,
    ):
        """
        GIVEN a range through stdin input but it corresponds to no commits
        WHEN the command is run
        THEN it should warn no commits were found and return 0
        """
        scan_commit_range_mock.return_value = 0
        get_list_mock.return_value = []

        result = cli_fs_runner.invoke(
            cli, ["-v", "scan", "pre-receive"], input="bbbb\naaaa\norigin/main\n"
        )
        get_list_mock.assert_called_once_with("--max-count=51 bbbb" + "..." + "aaaa")
        scan_commit_range_mock.assert_not_called()
        assert (
            "Unable to get commit range.\n  before: bbbb\n  after: aaaa\nSkipping pre-receive hook\n\n"
            in result.output
        )
        assert result.exit_code == 0

    @patch("ggshield.pre_receive_cmd.get_list_commit_SHA")
    @patch("ggshield.pre_receive_cmd.scan_commit_range")
    @patch("ggshield.pre_receive_cmd.check_git_dir")
    def test_stdin_breakglass_2ndoption(
        self,
        check_dir_mock: Mock,
        scan_commit_range_mock: Mock,
        get_list_mock: Mock,
        cli_fs_runner: CliRunner,
    ):
        """
        GIVEN 20 commits through stdin input but breakglass active
        WHEN the command is run
        THEN it should return 0
        """
        get_list_mock.return_value = ["a" for _ in range(20)]

        result = cli_fs_runner.invoke(
            cli,
            ["-v", "scan", "pre-receive"],
            input="bbbb\naaaa\norigin/main\n",
            env={
                "GIT_PUSH_OPTION_COUNT": "2",
                "GIT_PUSH_OPTION_0": "unrelated",
                "GIT_PUSH_OPTION_1": "breakglass",
            },
        )
        get_list_mock.assert_not_called()
        scan_commit_range_mock.assert_not_called()
        assert (
            "SKIP: breakglass detected. Skipping GitGuardian pre-receive hook.\n"
            in result.output
        )
        assert result.exit_code == 0

    @patch("ggshield.pre_receive_cmd.get_list_commit_SHA")
    @patch("ggshield.pre_receive_cmd.scan_commit_range")
    @patch("ggshield.pre_receive_cmd.check_git_dir")
    def test_stdin_input_empty(
        self,
        check_dir_mock: Mock,
        scan_commit_range_mock: Mock,
        get_list_mock: Mock,
        cli_fs_runner: CliRunner,
    ):
        """
        GIVEN an empty stdin input
        WHEN the command is run
        THEN it should raise an error and return 1
        """

        result = cli_fs_runner.invoke(cli, ["-v", "scan", "pre-receive"], input="")
        assert result.exit_code == 1
        assert "Error: Invalid input arguments: []\n" in result.output

    @patch("ggshield.pre_receive_cmd.get_list_commit_SHA")
    @patch("ggshield.pre_receive_cmd.scan_commit_range")
    @patch("ggshield.pre_receive_cmd.check_git_dir")
    def test_stdin_input_creation(
        self,
        check_dir_mock: Mock,
        scan_commit_range_mock: Mock,
        get_list_mock: Mock,
        cli_fs_runner: CliRunner,
    ):
        """
        GIVEN a ref creation event
        WHEN the command is run
        THEN it should scan the last 50 commits
        """

        scan_commit_range_mock.return_value = 0
        get_list_mock.return_value = ["a" for _ in range(60)]

        result = cli_fs_runner.invoke(
            cli, ["-v", "scan", "pre-receive"], input=f"{EMPTY_SHA}\n{'a'*40}\nmain"
        )

        assert "New tree event. Scanning last 50 commits" in result.output
        assert "Commits to scan: 50" in result.output
        assert result.exit_code == 0
        get_list_mock.assert_called_once_with(
            f"--max-count=51 {EMPTY_TREE} { 'a' * 40}"
        )
        scan_commit_range_mock.assert_called_once()

    @patch("ggshield.pre_receive_cmd.get_list_commit_SHA")
    @patch("ggshield.pre_receive_cmd.scan_commit_range")
    @patch("ggshield.pre_receive_cmd.check_git_dir")
    def test_stdin_input_deletion(
        self,
        check_dir_mock: Mock,
        scan_commit_range_mock: Mock,
        get_list_mock: Mock,
        cli_fs_runner: CliRunner,
    ):
        """
        GIVEN a deletion event
        WHEN the command is run
        THEN it should return 0 and indicate nothing to do
        """

        result = cli_fs_runner.invoke(
            cli, ["-v", "scan", "pre-receive"], input=f"{'a'*40} {EMPTY_SHA}  main"
        )
        assert result.exit_code == 0
        assert "Deletion event or nothing to scan.\n" in result.output

    @patch("ggshield.pre_receive_cmd.get_list_commit_SHA")
    @patch("ggshield.pre_receive_cmd.scan_commit_range")
    @patch("ggshield.pre_receive_cmd.check_git_dir")
    def test_stdin_input_no_newline(
        self,
        check_dir_mock: Mock,
        scan_commit_range_mock: Mock,
        get_list_mock: Mock,
        cli_fs_runner: CliRunner,
    ):
        """
        GIVEN 20 commits through stdin input
        WHEN the command is run
        THEN it should pass onto scan and return 0
        """
        scan_commit_range_mock.return_value = 0
        get_list_mock.return_value = ["a" for _ in range(20)]

        result = cli_fs_runner.invoke(
            cli,
            ["-v", "scan", "pre-receive"],
            input="649061dcda8bff94e02adbaac70ca64cfb84bc78 bfffbd925b1ce9298e6c56eb525b8d7211603c09 refs/heads/main",  # noqa: E501
        )
        get_list_mock.assert_called_once_with(
            "--max-count=51 649061dcda8bff94e02adbaac70ca64cfb84bc78...bfffbd925b1ce9298e6c56eb525b8d7211603c09"  # noqa: E501
        )  # noqa: E501
        scan_commit_range_mock.assert_called_once()
        assert "Commits to scan: 20" in result.output
        assert result.exit_code == 0
