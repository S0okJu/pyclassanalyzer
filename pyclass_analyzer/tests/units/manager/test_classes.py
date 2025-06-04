from pyclass_analyzer.manager import ClassRecordManager, ClassRecord

class TestClassRecordManager:
    def test_add_success(self):
        manager = ClassRecordManager()
        record = ClassRecord("TestClass", "test_module")
        manager.add(record)
        assert manager.get("test_module.TestClass") == record

    def test_get_success(self):
        manager = ClassRecordManager()
        record = ClassRecord("TestClass", "test_module")
        manager.add(record)
        assert manager.get("test_module.TestClass") == record

    def test_get_by_name_success(self):
        manager = ClassRecordManager()
        record = ClassRecord("TestClass", "test_module")
        manager.add(record)
        assert manager.get_by_name("TestClass") == [record]

    def test_get_by_name_not_found(self):
        manager = ClassRecordManager()
        assert manager.get_by_name("TestClass") == []