from database import connect_db
import threading

class TerneryTreeNode:

    def __init__(self, ch, flag):
        self.ch = ch
        self.flag = flag
        self.left = 0
        self.right = 0
        self.center = 0

    def Add(self, string, node):
        key = string[0]

        if node == 0:
            node = TerneryTreeNode(key, 0)

        if key < node.ch:
            node.left = node.Add(string, node.left)
        elif key > node.ch:

            node.right = node.Add(string, node.right)
        else:

            if len(string) == 1:
                node.flag = 1
            else:
                node.center = node.Add(string[1:], node.center)

        return node

    def spdfs(self, match, ansList):
        if self.flag == 1:
            ansList.append(match)

        if self.center == 0 and self.left == 0 and self.right == 0:
            return

        if self.center != 0:
            self.center.spdfs(match + self.center.ch, ansList)

        if self.right != 0:
            self.right.spdfs(match[:-1] + self.right.ch, ansList)

        if self.left != 0:
            self.left.spdfs(match[:-1] + self.left.ch, ansList)

    def search(self, string, match, ansList):
        if len(string) > 0:
            key = string[0]

            if key < self.ch:
                if self.left == 0:
                    return 'No Match Found'
                self.left.search(string, match, ansList)
            elif key > self.ch:

                if self.right == 0:
                    return 'Not Match Found'
                self.right.search(string, match, ansList)
            else:

                if len(string) == 1:
                    if self.flag == 1:
                        ansList.append(match + self.ch)

                    if self.center != 0:
                        self.center.spdfs(match + self.ch
                                + self.center.ch, ansList)
                    return 'check'

                self.center.search(string[1:], match + key, ansList)
                return
        else:
            return 'Invalid String'

class AutoCompleteProvider:
    def __init__(self):
        self.root_node = TerneryTreeNode('', 0)
        self.lock = threading.Lock()

    def insert(self, name):
        self.root_node.Add(name.lower(), self.root_node)

    def insert_product(self, name):
        self.insert(name)
        for token in name.split(" "):
            if len(token) > 2:
                self.insert(token)

    def insert_product_safe(self, name):
        self.lock.acquire()
        self.insert_product(name)
        self.lock.release()

    def load_candidates(self):
        print "Generating autocomplete tree..."

        db = connect_db()
        cur = db.cursor()
        cur.execute("SELECT DISTINCT Name FROM Product")
        candidates = cur.fetchall()

        for candidate in candidates:
            self.insert_product(candidate[0])

        print "AutoCompleteProvider loaded"
        db.close()

    def autocomplete(self, keyword):
        result = []
        self.root_node.search(keyword.lower(), '', result)
        result.sort()
        return result[0:10]