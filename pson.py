# -*- coding:utf-8 -*-
# 解决大数据 json 转一维链表进行增删改的数据结构，既能快速进行顺序结构调整，
# 也能在本地存储时通过二进制作初步加密。
#

import ctypes
# value = 'hello world'  # 定义一个字符串变量
# address = id(value)  # 获取value的地址，赋给address
# get_value = ctypes.cast(address, ctypes.py_object).value  # 读取地址中的变量
# print(address,get_value)

# def get_value(address):
#     return ctypes.cast(address, ctypes.py_object).value
#
#
# def get_id(obj):
#     return id(obj)
# 该方法测试中存在问题， 内存地址id不是不变的，会根据存储数据类型发生变化

# import pickle
# 下列类型可以被封存：
#
# None, True 和 False;
#
# 整数、浮点数、复数；
#
# 字符串、字节串、字节数组；
#
# 只包含可封存对象的元组、列表、集合和字典；
#
# 可在模块最高层级上访问的（内置与用户自定义的）函数（使用 def，而不是使用 lambda 定义）;
#
# 可在模块最高层级上访问的类；
#
# instances of such classes whose the result of calling __getstate__() is picklable (see section 封存类实例 for details).
#
# 尝试封存不能被封存的对象会抛出 PicklingError 异常，

import pickle


def get_value(bytes_obj):
    return pickle.loads(bytes_obj)


def save_val(obj):
    return pickle.dumps(obj)


# 规则定义如下
'''
初始化时
第一个节点 pre=0 
最后一个节点 next=0
position 从 1 开始递增 但最终结果中未必是第一个或最后一个节点
'''


class PsonItem:
    def __init__(self, position: int, pre: int, next: int, val_addr):
        self.position = position
        self.pre = pre
        self.next = next
        self.val_addr = val_addr

    def __str__(self):
        str = ""
        str += "{position:%s, pre:%s, next:%s, val: %s}" % \
               (self.position, self.pre, self.next, self.val_addr)
        return str


# 存放每一个 PsonItem  和 position  的映射关系
class PsonHash:
    def __init__(self, head: int, tail: int, all: dict, index: int):
        self.head = head
        self.tail = tail
        self.all = all
        self.index = index  # 控制主键自增，不会随着修改和删除而改变，只在插入时变化。

    def __len__(self):
        return len(self.all)

    def get_addr_from_hash(self, position):
        if position in self.all.keys():
            return self.all[position]
        else:
            return None

    def get_val_from_hash(self, position):
        if position in self.all.keys():
            return self.all[position]
        else:
            return None


class PsonArray:
    def __init__(self, head=0, tail=0, hash_dict={}, index=0):
        self.hash = PsonHash(head, tail, hash_dict, index)

    def __len__(self):
        return len(self.hash)

    def __str__(self):
        str = ""
        for k, v in  self.hash.all.items():
            str += "{position:%s, pre:%s, next:%s}" % (k, v.pre, v.next)
        return str

    def getitem(self, position):
        val = self.hash.get_val_from_hash(position)
        return val


    # 在首部加入新节点
    def prepend(self, obj):
        # 对象转地址
        val = save_val(obj)
        # 构建 Pson_item
        item = PsonItem(1, 0, 0, val)
        # 写入查询 hash
        self.hash.head = 1
        self.hash.tail = 1
        self.hash.index = 1
        self.hash.all[1] = item

    # 在某个节点后插入新节点
    def insert_item(self, insert_position, obj):
        # 待插入对象转地址
        val_addr = save_val(obj)
        if insert_position == 0:
            # 取出原头节点
            head_item = self.getitem(self.hash.head)
            # 构建 Pson_item
            position = self.hash.index + 1
            item = PsonItem(position, 0, head_item.position,
                            val_addr)
            self.hash.all[position] = item
            head_item.pre = position
            self.hash.all[head_item.position] = head_item
            self.hash.index = position
            self.hash.head = position
        else:
            # 取出待插入节点
            pre_item = self.getitem(insert_position)
            # print(pre_item)
            if pre_item.next != 0:
                next_item = self.getitem(pre_item.next)
                position = self.hash.index + 1
                # 构建 Pson_item
                item = PsonItem(position,
                                pre_item.position,
                                next_item.position,
                                val_addr)
                self.hash.all[position] = item
                self.hash.index = position
                # 前后位置关系改变
                pre_item.next = position
                self.hash.all[insert_position] = pre_item
                next_item.pre = position
                self.hash.all[next_item.position] = next_item

            else:
                # 构建 Pson_item
                position = self.hash.index + 1
                item = PsonItem(position,
                                pre_item.position,
                                0,
                                val_addr)
                self.hash.all[position] = item
                self.hash.index = position
                # 前后位置关系改变
                pre_item.next = position
                self.hash.tail = position
                self.hash.all[insert_position] = pre_item

    def append(self, obj):
        if self.hash.head == 0 and self.hash.tail == 0:
            self.prepend(obj)
        elif self.hash.tail != 0:
            insert_position = self.hash.tail
            self.insert_item(insert_position, obj)

    def remove(self, position):
        assert position > 0
        remove_item = self.getitem(position)
        if remove_item:
            # 针对头节点：
            if remove_item.pre == 0:
                next_item = self.getitem(remove_item.next)
                next_item.pre = 0
                self.hash.all[next_item.position] = next_item
                self.hash.head = next_item.position
            # 针对尾节点：
            elif remove_item.next == 0:
                pre_item = self.getitem(remove_item.pre)
                pre_item.next = 0
                self.hash.all[pre_item.position] = pre_item
                self.hash.tail = pre_item.position
            # 针对中间节点：
            else:
                # 前后节点
                pre_item = self.getitem(remove_item.pre)
                next_item = self.getitem(remove_item.next)
                # 前后位置关系改变
                pre_item.next = next_item.position
                next_item.pre = pre_item.position
                self.hash.all[pre_item.position] = pre_item
                self.hash.all[next_item.position] = next_item
            # 对象设为 None 释放内存
            self.hash.all[position] = None
            # 从 hash 中移除键
            self.hash.all.pop(position)
            return True
        else:
            return False

    def modify(self, position, obj):
        modify_item = self.getitem(position)
        if modify_item:
            old_obj = get_value(modify_item.val_addr)
            old_obj = None
            val_addr = save_val(obj)
            modify_item.val_addr = val_addr
            self.hash.all[position] = modify_item
            return True
        else:
            return False

    def exchange(self, position1, position2):

        # 将两个位置的节点交换
        item1 = self.getitem(position1)
        assert item1 is not None
        item2 = self.getitem(position2)
        assert item2 is not None
        
        item1_pre = self.getitem(item1.pre)
        item1_next = self.getitem(item1.next)
        item2_pre = self.getitem(item2.pre)
        item2_next = self.getitem(item2.next)

        if item1_pre:
            item1_pre.next = position2
            self.hash.all[item1_pre.position] = item1_pre
        else:
            item2.pre = 0
            item2.next = item1_next.position
            item1.pre = item2_pre.position
            self.hash.head = position2

        if item1_next:
            item1_next.pre = position2
            self.hash.all[item1_next.position] = item1_next
        else:
            item2.next = 0
            self.hash.tail = position2
            
        if item2_pre:
            item2_pre.next = position1
            self.hash.all[item2_pre.position] = item2_pre
        else:
            item1.pre = 0
            item1.next = item2_next.position
            item2.pre = item1_pre.postion
            self.hash.head = position1
            
        if item2_next:
            item2_next.pre = position1
            self.hash.all[item2_next.position] = item2_next
        else:
            item1.next = 0
            item1.pre = item2_pre.position
            item2.next = item1_next.position
            self.hash.tail = position1

        if item1.pre and item2_pre:
            if item1.position == item2_pre.position:
                item1.pre = position2
            else:
                item1.pre = item2_pre.position

        if item1.next and item2_next:
            item1.next = item2_next.position
        if item2.pre and item1_pre:
            item2.pre = item1_pre.position

        if item2.next and item1_next:
            if item2.position == item1_next.position:
                item2.next = position1
            else:
                item2.next = item1_next.position
            
        self.hash.all[item1.position] = item1
        self.hash.all[item2.position] = item2

    def query(self, key):
        for v in self.hash.all.values():
            if get_value(v.val_addr) == key:
                return v.position
        return None

    def order_list(self):
        result = list()
        head_p = self.hash.head
        item = self.getitem(head_p)
        while item is not None:
            result.append(item)
            item = self.getitem(item.next)
        return result

    def show_array(self):
        ordered_array = self.order_list()
        print("len:%s" % len(ordered_array))
        for o in ordered_array:
            print(o)


class PsonReader:
    def __init__(self, filename):
        self.filename = filename
        self.position = 0

    def load_pson(self):
        try:
            with open(self.filename, 'rb') as f:
                objects = pickle.load(f)
        except EOFError:
            raise EOFError
        head = objects.hash.head
        tail = objects.hash.tail
        index = objects.hash.index
        dict = objects.hash.all
        array = PsonArray(head, tail, dict, index)
        if self.position == 0:
            self.position = head
        else:
            item = array.getitem(self.position)
            self.position = item.next
        return objects, self.position

    def __getstate__(self):
        # Copy the object's state from self.__dict__ which contains
        # all our instance attributes. Always use the dict.copy()
        # method to avoid modifying the original state.
        state = self.__dict__.copy()
        # Remove the unpicklable entries.
        del state['filename']
        del state['position']
        return state

    def __setstate__(self, state):
        # Restore instance attributes (i.e., filename and lineno).
        self.__dict__.update(state)
        # Restore the previously opened file's state. To do so, we need to
        # reopen it and read from it until the line count is restored.


# test 测试方法
if __name__ == "__main__":
    # 初始化对象
    array = PsonArray()
    # 测试连续插入变化的字符串：
    print("$$$$ 测试连续 append 对象 $$$$")
    for i in range(10):
        test_obj = {
            'val': 'abc_%s' % i
        }
        array.append(test_obj)
        # print(array)
    print(array)
    print(len(array))

    print("$$$$ 验证获取指定位置的值 $$$$")
    position_array = [1, 9, 10, 11]
    for p in position_array:
        item = array.getitem(p)
        if item:
            print(item.val_addr)
            print(get_value(item.val_addr))

    print("$$$$ 验证通过 val 对象反查 position  $$$$")
    print(array.query({
            'val': 'abc_6'
        }))
    print(array.query({
        'val': 'abc_61'
    }))

    print("$$$$ 验证修改指定位置对象  $$$$")
    new_val={
        'val': 'abc_99'
    }
    array.modify(9, new_val)
    item = array.getitem(9)
    print(get_value(item.val_addr))

    print("$$$$ 验证插入指定位置对象  $$$$")
    insert_val={
        'val': 'abc_88'
    }
    array.insert_item(8, insert_val)
    array.show_array()

    print("$$$$ 验证继续插入指定位置对象  $$$$")
    test_val={
        'val': 'abc_55'
    }
    array.insert_item(5, test_val)
    array.show_array()

    print("$$$$ 验证继续插入头部位置对象  $$$$")
    head_val={
        'val': 'abc_00'
    }
    array.insert_item(0, head_val)
    array.show_array()

    print("$$$$ 验证删除指定位置对象  $$$$")
    remove_p = 2
    array.remove(remove_p)
    array.show_array()
    print("$$$$ 验证删除头部位置对象  $$$$")
    head_p = array.hash.head
    array.remove(head_p)
    array.show_array()
    print("$$$$ 验证删除尾部位置对象  $$$$")
    tail_p = array.hash.tail
    array.remove(tail_p)
    array.show_array()

    print("$$$$ 验证交换位置方法 - 不相邻情况 $$$$")
    array.exchange(4, 6)
    array.show_array()

    print("$$$$ 验证交换位置方法 - 相邻情况 $$$$")
    array.exchange(7, 8)
    array.show_array()

    print("$$$$ 验证交换位置方法 - 头部情况 $$$$")
    array.exchange(1, 12)
    array.show_array()

    print("$$$$ 验证交换位置方法 - 尾部情况 $$$$")
    array.exchange(4, 9)
    array.show_array()

    print("$$$$ 验证交换位置方法 - 头尾情况 $$$$")
    array.exchange(12, 4)
    array.show_array()

    print("$$$$ 验证 文件存储对象 $$$$")
    with open('pickle_test.txt','wb') as file:
        pickle.dump(array, file)

    print("$$$$ 验证 文件读取，并且可以按顺序读取 $$$$")
    reader = PsonReader("pickle_test.txt")
    for step in range(5):
        objects, position = reader.load_pson()
        print(position)

    # 读取 json 文件 转 pson
    import json
    with open('test.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        print(data)
        test_array = PsonArray()
        for d in data:
            test_array.append(d)
        test_array.show_array()
        with open('test_pson.txt', 'wb') as file:
            pickle.dump(array, file)
        item = test_array.getitem(1122)
        print(item)
        if item:
            print(item.val_addr)
            print(get_value(item.val_addr))