import camel_split
import collections

import javalang
import json
from tqdm import tqdm
import copy

from collections import Counter
import pickle

def normalize(s):
    return s[0].lower() + s[1:]


def add_split_method_name(original_ast_outputs):
    method_name = original_ast_outputs[0]['value']
    original_ast_outputs[0].pop('value')
    tokens = camel_split.tokenize(method_name)
    tokens_normal = list(map(normalize, tokens))

    current_id = original_ast_outputs[-1]['id']
    add_id_list = []
    for token in tokens_normal:
        d = collections.OrderedDict()
        current_id += 1
        d["id"] = current_id
        add_id_list.append(current_id)
        d["type"] = 'SplitMethodToken'
        d['value'] = token
        original_ast_outputs.append(d)
    if 'children' in original_ast_outputs[0].keys():
        original_ast_outputs[0]['children'] = add_id_list + original_ast_outputs[0]['children']
    else:
        original_ast_outputs[0]['children'] = add_id_list

    modified_ast_outputs = original_ast_outputs
    return modified_ast_outputs


def add_split_invocation_name(original_ast_outputs):
    for node in original_ast_outputs:
        if node['type'] == 'MethodInvocation':
            if '.' not in node['value']:
                tokens = camel_split.tokenize(node['value'])
                tokens_normal = list(map(normalize, tokens))
                node['value'] = ""

                current_id = original_ast_outputs[-1]['id']
                add_id_list = []
                for token in tokens_normal:
                    d = collections.OrderedDict()
                    current_id += 1
                    d["id"] = current_id
                    add_id_list.append(current_id)
                    d["type"] = 'SplitInvocationToken'
                    d['value'] = token
                    original_ast_outputs.append(d)

                if 'children' in node.keys():
                    node['children'] = add_id_list + node['children']
                else:
                    node['children'] = add_id_list

            else:
                value_tokens_list = node['value'].split('.')
                node['value'] = value_tokens_list[0]
                invocation_name = value_tokens_list[1]
                if invocation_name == '_1':
                    print('qqq')
                tokens = camel_split.tokenize(invocation_name)
                tokens_normal = list(map(normalize, tokens))

                current_id = original_ast_outputs[-1]['id']
                add_id_list = []
                for token in tokens_normal:
                    d = collections.OrderedDict()
                    current_id += 1
                    d["id"] = current_id
                    add_id_list.append(current_id)
                    d["type"] = 'SplitInvocationToken'
                    d['value'] = token
                    original_ast_outputs.append(d)

                if 'children' in node.keys():
                    node['children'] = add_id_list + node['children']
                else:
                    node['children'] = add_id_list

    modified_ast_outputs = original_ast_outputs
    return modified_ast_outputs


def code_to_ast(new_code, code, errornum, operatenum):
    tokens = javalang.tokenizer.tokenize(new_code)
    token_list = list(javalang.tokenizer.tokenize(new_code))


    # reduce the size of word list
    for i in range(len(token_list)):
        # print(type(token_list[i]),'|',token_list[i],'|',token_list[i].value)
        if type(token_list[i]) is javalang.tokenizer.String \
                or type(token_list[i]) is javalang.tokenizer.Character:
            token_list[i].value = '<STR>'
        if type(token_list[i]) is javalang.tokenizer.Integer \
                or type(token_list[i]) is javalang.tokenizer.DecimalInteger \
                or type(token_list[i]) is javalang.tokenizer.OctalInteger \
                or type(token_list[i]) is javalang.tokenizer.BinaryInteger \
                or type(token_list[i]) is javalang.tokenizer.HexInteger \
                or type(token_list[i]) is javalang.tokenizer.FloatingPoint \
                or type(token_list[i]) is javalang.tokenizer.DecimalFloatingPoint \
                or type(token_list[i]) is javalang.tokenizer.HexFloatingPoint:
            token_list[i].value = '<NUM>'

    tokens = (i for i in token_list)

    length = len(token_list)
    parser = javalang.parser.Parser(tokens)
    try:
        tree = parser.parse_member_declaration()
    except (javalang.parser.JavaSyntaxError, IndexError, StopIteration, TypeError):
        print(new_code)

        tokens = javalang.tokenizer.tokenize(code)
        token_list = list(javalang.tokenizer.tokenize(code))


        for i in range(len(token_list)):
                #print(type(token_list[i]),'|',token_list[i],'|',token_list[i].value)
                if type(token_list[i]) is javalang.tokenizer.String \
                        or type(token_list[i]) is javalang.tokenizer.Character:
                        token_list[i].value = '<STR>'
                if type(token_list[i]) is javalang.tokenizer.Integer \
                        or type(token_list[i]) is javalang.tokenizer.DecimalInteger \
                        or type(token_list[i]) is javalang.tokenizer.OctalInteger \
                        or type(token_list[i]) is javalang.tokenizer.BinaryInteger \
                        or type(token_list[i]) is javalang.tokenizer.HexInteger \
                        or type(token_list[i]) is javalang.tokenizer.FloatingPoint \
                        or type(token_list[i]) is javalang.tokenizer.DecimalFloatingPoint \
                        or type(token_list[i]) is javalang.tokenizer.HexFloatingPoint:
                        token_list[i].value = '<NUM>'

        tokens = (i for i in token_list)


        length = len(token_list)
        parser = javalang.parser.Parser(tokens)

        tree = parser.parse_member_declaration()

        errornum+=1

        # continue
    flatten = []
    for path, node in tree:
        flatten.append({'path': path, 'node': node})

    outputs = []
    for i, Node in enumerate(flatten):
        d = collections.OrderedDict()
        path = Node['path']
        node = Node['node']
        children = []
        for child in node.children:
            child_path = None
            if isinstance(child, javalang.ast.Node):
                child_path = path + tuple((node,))
                for j in range(i + 1, len(flatten)):
                    if child_path == flatten[j]['path'] and child == flatten[j]['node']:
                        children.append(j)
            if isinstance(child, list) and child:
                child_path = path + (node, child)
                for j in range(i + 1, len(flatten)):
                    if child_path == flatten[j]['path']:
                        children.append(j)
        d["id"] = i
        d["type"] = str(node)
        if children:
            d["children"] = children
        value = None
        if hasattr(node, 'name'):
            value = node.name
        elif hasattr(node, 'value'):
            value = node.value
        elif hasattr(node, 'position') and node.position:
            for i, token in enumerate(token_list):
                if node.position == token.position:
                    pos = i + 1
                    value = str(token.value)
                    while pos < length and token_list[pos].value == '.':
                        value = value + '.' + token_list[pos + 1].value
                        pos += 2
                    break
        elif type(node) is javalang.tree.This \
                or type(node) is javalang.tree.ExplicitConstructorInvocation:
            value = 'this'
        elif type(node) is javalang.tree.BreakStatement:
            value = 'break'
        elif type(node) is javalang.tree.ContinueStatement:
            value = 'continue'
        elif type(node) is javalang.tree.TypeArgument:
            value = str(node.pattern_type)
        elif type(node) is javalang.tree.SuperMethodInvocation \
                or type(node) is javalang.tree.SuperMemberReference:
            value = 'super.' + str(node.member)
        elif type(node) is javalang.tree.Statement \
                or type(node) is javalang.tree.BlockStatement \
                or type(node) is javalang.tree.ForControl \
                or type(node) is javalang.tree.ArrayInitializer \
                or type(node) is javalang.tree.SwitchStatementCase:
            value = 'None'
        elif type(node) is javalang.tree.VoidClassReference:
            value = 'void.class'
        elif type(node) is javalang.tree.SuperConstructorInvocation:
            value = 'super'

        if value is not None and type(value) is type('str'):
            d['value'] = value
 
        if not children and not value:
            print('Leaf has no value!')
            print(type(node))
            return False, 1

        outputs.append(d)

    # # mokaizo 1.7
    # temp_outputs = copy.deepcopy(outputs)
    # outputs = add_split_method_name(temp_outputs)
    # # mokaizo 1.14
    # outputs = add_split_invocation_name(temp_outputs)

    operatenum += 1

    return True, outputs, errornum, operatenum


def SBT(cur_root_id, node_list):
    cur_root = node_list[cur_root_id]
    tmp_list = []
    tmp_list.append("(")
    if 'value' in cur_root and cur_root['value'] != 'None':
        value = cur_root['value']
        str = cur_root['type'] + '_' + value
    else:
        str = cur_root['type']
    tmp_list.append(str)

    if 'children' in cur_root:
        chs = cur_root['children']
        for ch in chs:
            tmp_list.extend(SBT(ch, node_list))
    tmp_list.append(")")
    tmp_list.append(str)
    return tmp_list


def ast_to_sbt(ast):
    return SBT(0, ast)


def code_to_sbt_chunk(json_data, sbt_file='sbt', nl_file='nl'):
    unicodecount = 0
    with open(sbt_file, 'w+') as sbt_file, open(nl_file, 'w+') as nl_file:
        ign_cnt = 0
        sbt_id = 1
        with open(json_data, 'r') as data_chunk:
            chunk = data_chunk.readlines()
        # for idx, line in enumerate(tqdm(json_data)):
            for _, line in enumerate(tqdm(chunk)):
                line_json = eval(line)
                raw_code = line_json['code']
                raw_code.replace('\n', ' ')
                code = raw_code.strip()

                modify_code = line_json['result']
                modify_code.replace('\n', ' ')
                modify_code = modify_code.strip()

                nl = line_json['nl']

                flag, value, errorNum, OperateNum = code_to_ast(modify_code, code, errorNum, OperateNum)
                if flag:
                    ast = value
                    sbt = ast_to_sbt(ast)

                    try:
                        sbt_file.write(str(sbt_id) + '\t')
                        sbt_file.write(' '.join(sbt) + '\n')
                        nl_file.write(str(sbt_id) + '\t')
                        nl_file.write(nl + '\n')
                        sbt_id += 1
                    except UnicodeEncodeError as e:
                        unicodecount += 1
                        #num, ast = a.split('\t')
                        print('-------------Number', unicodecount)
                        print(ast)
                        #print(ast_sbt)
                        # continue
                else:
                    if value == 1:
                        ign_cnt += 1

        print("ign_cnt", ign_cnt)
        print('UnicodeEncodeError Number: ', unicodecount)
       


def code_to_sbt(json_data, sbt_file='sbt', nl_file='nl'):
    unicodecount = 0
    errorNum = 0
    OperateNum = 0
    with open(sbt_file, 'w+') as sbt_file, open(nl_file, 'w+') as nl_file:
        ign_cnt = 0
        sbt_id = 1
        for idx, line in enumerate(tqdm(json_data)):
            raw_code = line['code']
            raw_code.replace('\n', ' ')
            code = raw_code.strip()

            modify_code = line['result']
            modify_code.replace('\n', ' ')
            modify_code = modify_code.strip()

            nl = line['nl']

            flag, value, errorNum, OperateNum = code_to_ast(modify_code, code, errorNum, OperateNum)
            if flag:
                ast = value
                sbt = ast_to_sbt(ast)

                try:
                    sbt_file.write(str(sbt_id) + '\t')
                    sbt_file.write(' '.join(sbt) + '\n')
                    nl_file.write(str(sbt_id) + '\t')
                    nl_file.write(nl + '\n')
                    sbt_id += 1
                except UnicodeEncodeError as e:
                    unicodecount += 1
                    #num, ast = a.split('\t')
                    print('-------------Number', unicodecount)
                    print(ast)
                    #print(ast_sbt)
                    continue
            else:
                if value == 1:
                    ign_cnt += 1

        print("ign_cnt", ign_cnt)
        print('UnicodeEncodeError Number: ', unicodecount)
        print("Error Num: ",errorNum)
        print("Operate Num: ",OperateNum) 

def build_vocabulary(sbt_file='sbt', nl_file='nl', code_vocabulary='code_vocabulary', nl_vocabulary='nl_vocabulary'):
    sbt_vocabs = Counter()
    nl_vocabs = Counter()

    with open(sbt_file, 'r') as f:
        data = f.readlines()
        for item in tqdm(data):
            idx, sbt = item.split('\t', 1)
            sbt = sbt.strip()
            # print(sbt)
          
            sbt_vocab = sbt.split(' ')
            # sbt_vocab = set(sbt_vocab)
            # sbt_vocabs = sbt_vocabs | sbt_vocab
            sbt_vocabs.update(sbt_vocab)
 
    with open(code_vocabulary, 'w+') as f:
        special_words = ['<S>', '</S>', '<UNK>', '<KEEP>', '<DEL>', '<INS>', '<SUB>', '<NONE>']
        sbt_vocabs.update(special_words)

        for i in special_words:
            sbt_vocabs[i] = 2147483647


        for idx, vocab in enumerate((sbt_vocabs.most_common(60008))):
            f.write(vocab[0] + '\n')  


    with open(nl_file, 'r') as f:
        data = f.readlines()
        for item in tqdm(data):
            idx, nl = item.split('\t', 1)
            # print(nl[:-1])
            nl = nl[:-1]
            nl_vocab = nl.split(' ')
            # nl_vocab = set(nl_vocab)
            # nl_vocabs = nl_vocabs | nl_vocab
            nl_vocabs.update(nl_vocab)
            # print(nl_vocabs)

    with open(nl_vocabulary, 'w+') as f:
        special_words = ['<S>', '</S>', '<UNK>', '<KEEP>', '<DEL>', '<INS>', '<SUB>', '<NONE>']
        nl_vocabs.update(special_words)

        for i in special_words:
            nl_vocabs[i] = 2147483647

        for idx, nl in enumerate((nl_vocabs.most_common(60008))):
            f.write(nl[0] + '\n')  

if __name__ == "__main__":

    datapath = ""
    jsons = []
    # train data
    # with open(datapath+'train.json','r') as f:
    #     data = f.readlines()
    #     for item in data:
    #        jsons.append(eval(item))

    # # valid data
    # with open(datapath+'valid.json','r') as f:
    #     data = f.readlines()
    #     for item in data:
    #        jsons.append(eval(item))

    # test data
    with open(datapath+'test.json','r') as f:
        data = f.readlines()
        for item in data:
           jsons.append(eval(item))

    # build sbt and nl files
    sbt_file = 'train.token.code'
    nl_file = 'train.token.nl'
    code_vocabulary = 'vocab.code'
    nl_vocabulary = 'vocab.nl'
    code_to_sbt(jsons, sbt_file=datapath+sbt_file, nl_file=datapath+nl_file)
    #build_vocabulary(sbt_file=datapath+sbt_file, nl_file=datapath+nl_file, code_vocabulary=datapath+code_vocabulary, nl_vocabulary=datapath+nl_vocabulary)
    print("finished!")