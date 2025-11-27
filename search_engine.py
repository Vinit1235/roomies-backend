class TrieNode:
    def __init__(self):
        self.children = {}
        self.room_ids = set()  # Store sets of Room IDs that match this prefix

class SearchTrie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, text, room_id):
        """Insert a text (title, location, college) linked to a room_id."""
        if not text:
            return
        
        text = text.lower()
        # We want to be able to search by any word in the text
        # e.g. "Sardar Patel" -> Search "Patel" should find it.
        # So we insert suffixes or just words?
        # Let's insert each word as a starting point for the Trie.
        words = text.split()
        for word in words:
            self._insert_word(word, room_id)

    def _insert_word(self, word, room_id):
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
            node.room_ids.add(room_id)

    def search(self, prefix):
        """Returns a set of room_ids that contain a word starting with prefix."""
        if not prefix:
            return set()
        
        prefix = prefix.lower()
        node = self.root
        for char in prefix:
            if char not in node.children:
                return set()
            node = node.children[char]
        
        return node.room_ids
