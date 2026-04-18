from __future__ import annotations

import random
from datetime import datetime, timedelta


def give_test(total: int, maxvalue: int) -> list[str]:
    result: list[str] = []
    while len(result) <= total:
        add = random.random() >= 0.3334
        while True:
            n1 = random.randint(5, maxvalue)
            n2 = random.randint(5, maxvalue)
            if add and n1 + n2 <= maxvalue:
                result.append(f"{n1:2d} + {n2:2d} = ")
                break
            if not add and n1 > n2:
                result.append(f"{n1:2d} - {n2:2d} = ")
                break
    return result


def give_bunchof_tests(number: int) -> None:
    for paper in range(number):
        rows = give_test(32, 100)
        print(f"Name: Harry    P{paper + 1}    Time:\t\t\t\tScore:")
        line = ""
        for index, item in enumerate(rows):
            if index % 4 == 0:
                print(line)
                line = ""
                print("\n")
            line += item + "       "
        print("\n\n")


def give_y2_test(total: int, divides: int, times: int, multiply: int, maxvalue: int):
    rows, answers = [], []
    while len(rows) < total - 1:
        t1 = random.randint(2, divides)
        t2 = random.randint(2, divides)
        t3 = random.randint(2, times)
        t4 = t1 * t2
        t5 = t2 * t3
        line = ""
        fraction = random.random() < 0.5
        if fraction:
            line += f"{t3}/{t1} × {t4:2d} "
        else:
            line += f"{t4:2d} ÷ {t1:2d} × {t3:2d} "

        add = random.random() >= 0.6667
        while True:
            n1 = t5
            n2 = random.randint(5, maxvalue)
            if add and n1 + n2 <= maxvalue:
                line += f"+ {n2:2d} = "
                rows.append(line)
                answers.append(n1 + n2)
                break
            if not add and n1 > n2:
                line += f"- {n2:2d} = "
                rows.append(line)
                answers.append(n1 - n2)
                break

    l1 = random.randint(10, multiply)
    l2 = random.randint(10, multiply)
    rows.append(f"×{l1}/{l2} = ")
    answers.append(l1 * l2)
    return rows, answers


def get_date(day: int) -> str:
    base_date = datetime.strptime("09/03/20", "%d/%m/%y")
    return (base_date + timedelta(days=day)).strftime("%A %d %b %Y")


def give_bunchof_y2_tests(number: int) -> None:
    with open("math.txt", "wt", encoding="utf-8") as questions:
        with open("answer.txt", "wt", encoding="utf-8") as answers_out:
            for paper in range(number):
                rows, answers = give_y2_test(12, 12, 20, 30, 1500)
                questions.write(f"Harry-{get_date(paper)}-Score:\n")
                answers_out.write(f"{get_date(paper)}\n")
                line = ""
                for index, item in enumerate(rows):
                    line += item + "            "
                    if (index + 1) % 3 == 0:
                        questions.write(line)
                        line = ""
                        questions.write("\n")
                    answers_out.write(f"{answers[index]},  ")
                questions.write("\n\n")
                answers_out.write("\n\n")
