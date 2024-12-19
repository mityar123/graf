import sys


def process_data(data):
    matrix = data

    return matrix


if __name__ == "__main__":
    if len(sys.argv) > 1:
        input_data = sys.argv[1]
        output_data = process_data(input_data)

        with open("output.txt", "w") as f:
            f.write(output_data)
