from pyclassanalyzer.utils.path import split_path


def test_split_path_relative_path_success():
    result = ['__init__.py']
    
    assert result == split_path("./pyclassanalyzer/__init__.py")

def test_split_path_absolute_path_success():
    test = "/User/test/test-folder/test.py"
    result = ['User', 'test', 'test-folder', 'test.py']
    
    assert result == split_path(test)