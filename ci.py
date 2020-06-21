#!/usr/bin/env python3
import re

class Error(Exception):
    """Base class for exceptions in this module."""
    pass

def count_space(s):
    space = 0
    for i in s:
        if i == ' ':
            space += 1
        else:
            break
    return space

def order_key(a, b):
    idx_dict = {}
    idx_dict["all"] = 0
    idx_dict["Spring"] = 1
    idx_dict["Summer"] = 2
    idx_dict["Fall"] = 3
    author_a, year_a, semester_a = a
    author_b, year_b, semester_b = b
    author_a = author_a.lower()
    author_b = author_b.lower()
    semester_idx_a = idx_dict[semester_a]
    semester_idx_b = idx_dict[semester_b]
    if year_a < year_b:
        return True
    if year_a > year_b:
        return False
    if year_a == year_b:
        if semester_idx_a < semester_idx_b:
            return True
        if semester_idx_a > semester_idx_b:
            return False
        if semester_idx_a == semester_idx_b:
            return author_a <= author_b

def check_sequence(chunk):
    seq = []
    for line in chunk:
        x = re.search("\[@(.*?), (.*?) (.*?)\]", line)
        author, year, semester = x.group(1), x.group(2), x.group(3)
        seq.append((author, year, semester))
        if semester not in ["Spring", "Fall", "all", "Summer"]:
            raise Error(f"unsupported semester {semester}")
    for i in range(len(seq) - 1):
        if not order_key(seq[i], seq[i + 1]):
            raise Error(f"list is not sorted: \n{chunk[i]}\n{chunk[i + 1]}")
    print(" ...OK")
    

def parse_bullet_list(chunk):
    valid_lines = list(filter(lambda x: len(x.strip()) != 0, chunk))
    space_list = list(map(count_space, valid_lines))
    if not space_list:
        return
    if min(space_list) == max(space_list):
        check_sequence(chunk)
    else:
        head_bullet = min(space_list)
        current_chunk = []
        bullet_name = None
        for (space, line) in zip(space_list, valid_lines):
            if space == head_bullet:
                if bullet_name:
                    print(f"Item: {bullet_name}")
                    parse_bullet_list(current_chunk)
                bullet_name = line.replace("*", "").strip()
                current_chunk = []
            else:
                current_chunk.append(line)
        print(f"Item: {bullet_name}")
        parse_bullet_list(current_chunk)

def parse_course(chunk):
    print(f"Course: {chunk[1].strip('#')}")
    parse_bullet_list(chunk[2:])

with open("README.md") as f:
    lines = list(map(lambda x: x.replace("\n", ""), f.readlines()))
    i = 0
    lst_line = 0
    chunked_line = []
    while i < len(lines):
        line = lines[i]
        if line.startswith("<a"):
            chunked_line.append(lines[lst_line:i])
            lst_line = i
        i += 1
    chunked_line.append(lines[lst_line:i])
    chunked_line = chunked_line[1:]
    for chunk in chunked_line:
        parse_course(chunk)
