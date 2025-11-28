def search(array: list[int], number: int) -> bool:
    if not array:
        return False

    left = 0
    right = len(array) - 1

    while right >= left:
        mid = left + (right - left) // 2
        if array[mid] > number:
            right = mid - 1
        elif array[mid] < number:
            left = mid + 1
        else:
            return True
    return False


temp_list = [1, 2, 3, 4, 6, 10, 22, 35, 50, 52, 53, 65, 100]

print(search(temp_list, 5))


