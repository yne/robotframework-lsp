def check_code_action_data_regression(data_regression, found, basename=None):
    import copy

    # For checking the test we need to make the uri/path the same among runs.
    found = copy.deepcopy(found)  # we don't want to change the initial data
    for c in found:
        arguments = c["arguments"]
        if arguments:
            for c in arguments:
                changes = c["edit"]["changes"]
                new_changes = {}
                for uri, v in changes.items():
                    uri = uri.split("/")[-1]
                    new_changes[uri] = v
                c["edit"]["changes"] = new_changes

    data_regression.check(found, basename=basename)


def _collect_errors(completion_context):
    from robotframework_ls.impl.code_analysis import collect_analysis_errors

    errors = [
        error.to_lsp_diagnostic()
        for error in collect_analysis_errors(completion_context)
    ]

    def key(diagnostic):
        return (
            diagnostic["range"]["start"]["line"],
            diagnostic["range"]["start"]["character"],
            diagnostic["message"],
        )

    errors = sorted(errors, key=key)
    return errors


def test_code_code_action_basic(workspace, libspec_manager, data_regression):
    from robotframework_ls.impl.completion_context import CompletionContext
    from robotframework_ls.impl.code_action import code_action

    workspace.set_root("case4", libspec_manager=libspec_manager, index_workspace=True)
    doc_import_from = workspace.put_doc("import_from_this_robot.robot")
    doc_import_from.source = """
*** Keywords ***
My Keyword
    No Operation
    
My Keyword not shown
    No Operation
"""

    doc = workspace.put_doc("case4.robot")
    doc.source = """
*** Test Cases ***
Some Test
    [Documentation]      Docs
    My Keyword"""

    errors = _collect_errors(CompletionContext(doc, workspace=workspace.ws))
    assert len(errors) == 1

    error = next(iter(errors))
    data = error["data"]
    assert data["kind"] == "undefined_keyword"

    end = error["range"]["end"]
    line = end["line"]
    col = end["character"]
    completion_context = CompletionContext(
        doc, workspace=workspace.ws, line=line, col=col
    )

    found_data = [data]
    actions = code_action(completion_context, found_data)
    check_code_action_data_regression(data_regression, actions)