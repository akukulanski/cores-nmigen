

def pack(buffer, elements, element_width):
    """
        pack generator groups the buffer in packets of "elements"
        considering they have "element_width" bit length.

        args:
            elements: how many elements do you want to join
            element_with: which is the width of each element
        example:
            a = [0, 1, 2, 3, 4, 5]
            b = [p for p in pack(a, 3, 8)]
            result: [0x020100, 0x050403]
    """
    adicionales = (elements - (len(buffer) % elements)) % elements
    buff = buffer + [0]*adicionales
    for i in range(0, len(buff), elements):
        b = 0
        for j in range(elements):
            b = (b << element_width) + buff[i+elements-j-1]
        yield b

def unpack(buffer, elements, element_width):
    """
        unpack generator ungroups the buffer items in "elements"
        parts of "element_with" bit length.

        args:
            elements: In how many parts do you want to split an item.
            element_with: bit length of each part.
        example:
            a = [0x020100, 0x050403]
            b = [p for p in unpack(a, 3, 8)]
            result: [0, 1, 2, 3, 4, 5,]]
    """
    mask = (1 << element_width) - 1
    for b in buffer:
        for _ in range(elements):
            yield (b & mask)
            b = b >> element_width
