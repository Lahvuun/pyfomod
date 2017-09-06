from copy import copy, deepcopy

from lxml import etree

import pyfomod
import pytest
from pyfomod import parser

# tests that need a modifiable tree should use schema_mod fixture and
# get the schema directly from pyfomod instead of using this variable
fomod_schema = pyfomod.FOMOD_SCHEMA_TREE


class Test_FomodElement:
    def test_element_get_max_occurs_normal(self, simple_parse):
        root = simple_parse[0]
        assert root._element_get_max_occurs(root._schema_element) == 1

    def test_element_get_max_occurs_unbounded(self, simple_parse):
        file_d = simple_parse[1][2][1]
        assert file_d._element_get_max_occurs(file_d._schema_element) is None

    def test_max_occ_default_value(self, simple_parse):
        root = simple_parse[0]
        assert root.max_occurences == 1

    def test_max_occ_unbounded(self, simple_parse):
        file_dep = simple_parse[1][2][1]
        assert file_dep.max_occurences is None

    def test_min_occ_default_value(self, simple_parse):
        root = simple_parse[1]
        assert root.min_occurences == 1

    def test_min_occ_normal_value(self, simple_parse):
        file_dep = simple_parse[1][2]
        assert file_dep.min_occurences == 0

    def test_type_none(self, simple_parse):
        root = simple_parse[0]
        assert root.type is None

    def test_type_simple_element(self, simple_parse):
        name = simple_parse[0][1]
        assert name.type == 'string'

    def test_type_complex_element(self, simple_parse):
        version = simple_parse[0][5]
        assert version.type == 'string'

    def test_comment_get_none(self, simple_parse):
        name = simple_parse[1][0]
        assert name.comment == ""

    def test_comment_get_normal(self, simple_parse):
        name = simple_parse[0][1]
        assert name.comment == " The name of the mod "

    def test_comment_set_none(self, conf_tree):
        name = conf_tree[0]
        assert name._comment is None
        name.comment = "comment"
        assert name.comment == "comment"

    def test_comment_set_normal(self, info_tree):
        name = info_tree[1]
        assert name.comment == " The name of the mod "
        name.comment = "comment"
        assert name.comment == "comment"

    def test_doc_normal(self, simple_parse):
        config = simple_parse[1]
        assert config.doc == "The main element containing the " \
            "module configuration info."

    def test_doc_none(self, simple_parse, schema_mod):
        config = simple_parse[1]
        config._schema_element.remove(config._schema_element[0])
        assert config.doc == ""

    def test_get_schema_doc_normal(self):
        doc = fomod_schema[-1][0][0].text
        assert parser.FomodElement._get_schema_doc(fomod_schema[-1]) == doc

    def test_get_schema_doc_none(self):
        assert parser.FomodElement._get_schema_doc(fomod_schema) is None

    def test_init_schema(self, simple_parse):
        for elem in simple_parse[0].iter(tag=etree.Element):
            assert elem._schema is pyfomod.FOMOD_SCHEMA_TREE

    def test_init_comment(self, simple_parse):
        name = simple_parse[0][1]
        assert name._comment is simple_parse[0][0]

    def test_get_order_from_group(self):
        group_elem = fomod_schema[4][1]
        result = parser.FomodElement._get_order_from_group(fomod_schema[5][1],
                                                           fomod_schema)
        assert group_elem is result

    def test_lookup_element_private_complex_type(self, simple_parse):
        root = simple_parse[0]
        current_lookups = (root._schema_element,
                           root._schema_type)
        assert current_lookups[0] is fomod_schema[-1]
        assert current_lookups[1] is fomod_schema[-1][1]

    def test_lookup_element_simple_element(self, simple_parse):
        name = simple_parse[0][1]
        current_lookups = (name._schema_element,
                           name._schema_type)
        assert current_lookups[0] is fomod_schema[-1][1][0][0]
        assert current_lookups[1] is fomod_schema[-1][1][0][0]

    def test_lookup_element_separate_complex_type(self, simple_parse):
        config = simple_parse[1]
        current_lookups = (config._schema_element,
                           config._schema_type)
        assert current_lookups[0] is fomod_schema[-2]
        assert current_lookups[1] is fomod_schema[-3]

    def test_lookup_element_group_order_tags(self, simple_parse):
        file_dep = simple_parse[1][2][1]
        current_lookups = (file_dep._schema_element,
                           file_dep._schema_type)
        assert current_lookups[0] is fomod_schema[4][1][0][0]
        assert current_lookups[1] is fomod_schema[2]

    def test_valid_attributes_simple_string(self, simple_parse):
        # a simple string attribute
        machine_version_attr = parser._Attribute("MachineVersion", None, None,
                                                 "string", "optional", None)
        version_elem = simple_parse[0][5]
        assert version_elem.valid_attributes() == [machine_version_attr]

    def test_valid_attributes_restriction(self, simple_parse):
        # fileDependency element (enumeration)
        state_rest_list = [parser._AttrRestElement('Missing',
                                                   "Indicates the mod file is"
                                                   " not installed."),
                           parser._AttrRestElement('Inactive', "Indicates the"
                                                   " mod file is installed, "
                                                   "but not active."),
                           parser._AttrRestElement('Active', "Indicates the "
                                                   "mod file is installed and"
                                                   " active.")]
        state_restrictions = parser._AttrRestriction('enumeration ',
                                                     state_rest_list,
                                                     None, None, None, None,
                                                     None, None, None, None,
                                                     None, None)
        file_dep_attrs = [parser._Attribute("file", "The file of the mod upon "
                                            "which a the plugin depends.",
                                            None, "string", "required", None),
                          parser._Attribute("state", "The state of the mod "
                                            "file.", None, "string",
                                            "required", state_restrictions)]
        file_dep_elem = simple_parse[1][2][1]
        assert file_dep_elem.valid_attributes() == file_dep_attrs

    def test_find_valid_attribute_normal(self, simple_parse):
        version = simple_parse[0][5]
        attr = parser._Attribute('MachineVersion', None, None,
                                 'string', 'optional', None)
        assert version._find_valid_attribute('MachineVersion') == attr

    def test_find_valid_attribute_valueerror(self, simple_parse):
        name = simple_parse[0][1]
        with pytest.raises(ValueError):
            name._find_valid_attribute('anyAttribute')

    def test_get_attribute_existing(self, simple_parse):
        mod_dep = simple_parse[1][2]
        assert mod_dep.get_attribute('operator') == 'And'

    def test_get_attribute_default(self, simple_parse):
        name = simple_parse[1][0]
        assert name.get_attribute('position') == 'Left'

    def test_set_attribute_normal(self, conf_tree):
        name = conf_tree[0]
        name.set_attribute('position', 'Right')
        assert name.get_attribute('position') == 'Right'

    def test_set_attribute_enum_restriction(self, conf_tree):
        name = conf_tree[0]
        with pytest.raises(ValueError):
            name.set_attribute('position', 'Top')

    def composite_dependency_valid_children(self):
        file_dep_child = parser._ChildElement('fileDependency', None, 1)
        flag_dep_child = parser._ChildElement('flagDependency', None, 1)
        game_dep_child = parser._ChildElement('gameDependency', 1, 0)
        fomm_dep_child = parser._ChildElement('fommDependency', 1, 0)
        dep_child = parser._ChildElement('dependencies', 1, 1)
        choice_ord = parser._OrderIndicator('choice',
                                            [file_dep_child, flag_dep_child,
                                             game_dep_child, fomm_dep_child,
                                             dep_child],
                                            None, 1)
        return parser._OrderIndicator('sequence', [choice_ord], 1, 1)

    def test_valid_children_parse_order(self):
        parse_order = parser.FomodElement._valid_children_parse_order
        sequence_ord = self.composite_dependency_valid_children()
        assert parse_order(fomod_schema[4][1]) == sequence_ord

    def test_valid_children_group_and_order(self, simple_parse):
        mod_dep = simple_parse[1][2]
        sequence_ord = self.composite_dependency_valid_children()
        assert mod_dep.valid_children() == sequence_ord

    def test_valid_children_none(self, simple_parse):
        name = simple_parse[0][1]
        assert name.valid_children() is None

    def test_find_possible_index_no_children(self):
        info = etree.fromstring("<fomod/>",
                                parser=parser.FOMOD_PARSER)
        assert info._find_possible_index('Name') == -1
        assert len(info) == 0

    def test_find_possible_index_none(self):
        conf = etree.fromstring("<config><moduleName/></config>",
                                parser=parser.FOMOD_PARSER)
        assert conf._find_possible_index('moduleName') is None
        assert len(conf) == 1

    def test_find_possible_index_invalid(self):
        info = etree.fromstring("<fomod/>",
                                parser=parser.FOMOD_PARSER)
        assert info._find_possible_index('any') is None
        assert len(info) == 0

    def test_find_possible_index_normal(self):
        info = etree.fromstring("<fomod><Name/><Version/></fomod>",
                                parser=parser.FOMOD_PARSER)
        assert info._find_possible_index('Author') == 1
        assert len(info) == 2

    def test_find_possible_index_fomodelement(self):
        info = etree.fromstring("<fomod/>",
                                parser=parser.FOMOD_PARSER)
        name = etree.SubElement(info, 'Name')
        info.remove(name)
        assert info._find_possible_index(name) == -1
        assert len(info) == 0

    def test_find_possible_index_valuerror(self):
        info = etree.fromstring("<fomod><Name/><Version/></fomod>",
                                parser=parser.FOMOD_PARSER)
        with pytest.raises(ValueError):
            info._find_possible_index(etree.Element('Author'))
        assert len(info) == 2

    def test_can_add_child(self):
        info = etree.fromstring("<fomod><Name/></fomod>",
                                parser=parser.FOMOD_PARSER)
        assert info.can_add_child('Author')
        assert not info.can_add_child('Name')

    def test_copy(self):
        root = etree.fromstring("<fomod attr='1'>text</fomod>",
                                parser=parser.FOMOD_PARSER)
        root_copy = copy(root)
        root_deep = deepcopy(root)
        assert root.tag == root_copy.tag == root_deep.tag
        assert root.text == root_copy.text == root_deep.text
        assert root.tail == root_copy.tail == root_deep.tail
        assert root.nsmap == root_copy.nsmap == root_deep.nsmap
        assert root.attrib == root_copy.attrib == root_deep.attrib

    def test_deepcopy_root(self):
        root = etree.fromstring("<fomod attr='1'/>",
                                parser=parser.FOMOD_PARSER)
        root_copy = deepcopy(root)
        assert root.tag == root_copy.tag
        assert root.text == root_copy.text
        assert root.tail == root_copy.tail
        assert root.nsmap == root_copy.nsmap
        assert root.attrib == root_copy.attrib

    def test_deepcopy_child(self):
        child = etree.fromstring("<fomod><Name>text</Name>tail</fomod>",
                                 parser=parser.FOMOD_PARSER)[0]
        child_copy = deepcopy(child)
        assert child.tag == child_copy.tag
        assert child.text == child_copy.text
        assert child.tail == child_copy.tail
        assert child.nsmap == child_copy.nsmap
        assert child.attrib == child_copy.attrib

    def test_deepcopy_children(self):
        root = etree.fromstring("<fomod><Name/><Author/><Version/></fomod>",
                                parser=parser.FOMOD_PARSER)
        root_copy = deepcopy(root)
        assert len(root) == len(root_copy)
        for index in range(0, len(root)):
            assert root[index].tag == root_copy[index].tag
            assert root[index].text == root_copy[index].text
            assert root[index].tail == root_copy[index].tail
            assert root[index].nsmap == root_copy[index].nsmap
            assert root[index].attrib == root_copy[index].attrib


class Test_FomodLookup:
    def test_base_class(self, simple_parse):
        for tree in simple_parse:
            for element in tree.iter(tag=etree.Element):
                assert isinstance(element, parser.FomodElement)

    def test_subclasses(self, simple_parse):
        root = simple_parse[1]
        assert isinstance(root, parser.Root)
        mod_dep = root.findall('.//moduleDependencies')
        assert(all(isinstance(elem, parser.Dependencies)) for elem in mod_dep)
        dep = root.findall('.//dependencies')
        assert(all(isinstance(elem, parser.Dependencies)) for elem in dep)
        vis = root.findall('.//visible')
        assert(all(isinstance(elem, parser.Dependencies)) for elem in vis)
        step = root.findall('.//installStep')
        assert(all(isinstance(elem, parser.InstallStep)) for elem in step)
        group = root.findall('.//group')
        assert(all(isinstance(elem, parser.Group)) for elem in group)
        plugin = root.findall('.//plugin')
        assert(all(isinstance(elem, parser.Plugin)) for elem in plugin)
        tp_dep = root.findall('.//dependencyType')
        assert(all(isinstance(elem, parser.TypeDependency)) for elem in tp_dep)
        tp_pat = root.findall('.//pattern/type')
        assert(all(isinstance(elem, parser.TypePattern)) for elem in tp_pat)
        fl_pat = root.findall('.//pattern/files')
        assert(all(isinstance(elem, parser.InstallPattern)) for elem in fl_pat)
