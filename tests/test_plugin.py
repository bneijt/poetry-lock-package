from cleo.testers.command_tester import CommandTester


def test_build_command_will_execute_plugin(tester: CommandTester) -> None:
    tester.execute()
