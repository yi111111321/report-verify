"""Minimal QR Code encoder (byte mode), dependency-free.

Supports model 2 symbols, versions 1-10, error correction levels L/M/Q/H.
Output is a boolean module matrix (True = dark) that can be rendered to PNG.
"""

from __future__ import annotations

ECL_L, ECL_M, ECL_Q, ECL_H = 0, 1, 2, 3

# Format-information two-bit values (not ordered like the enum).
_FORMAT_ECL_BITS = {ECL_L: 1, ECL_M: 0, ECL_Q: 3, ECL_H: 2}

# version -> ecl -> [(block_count, total_codewords_per_block, data_codewords_per_block)]
_RS_BLOCKS = {
    1: {ECL_L: [(1, 26, 19)], ECL_M: [(1, 26, 16)], ECL_Q: [(1, 26, 13)], ECL_H: [(1, 26, 9)]},
    2: {ECL_L: [(1, 44, 34)], ECL_M: [(1, 44, 28)], ECL_Q: [(1, 44, 22)], ECL_H: [(1, 44, 16)]},
    3: {ECL_L: [(1, 70, 55)], ECL_M: [(1, 70, 44)], ECL_Q: [(2, 35, 17)], ECL_H: [(2, 35, 13)]},
    4: {ECL_L: [(1, 100, 80)], ECL_M: [(2, 50, 32)], ECL_Q: [(2, 50, 24)], ECL_H: [(4, 25, 9)]},
    5: {ECL_L: [(1, 134, 108)], ECL_M: [(2, 67, 43)],
        ECL_Q: [(2, 33, 15), (2, 34, 16)], ECL_H: [(2, 33, 11), (2, 34, 12)]},
    6: {ECL_L: [(2, 86, 68)], ECL_M: [(4, 43, 27)],
        ECL_Q: [(4, 43, 19)], ECL_H: [(4, 43, 15)]},
    7: {ECL_L: [(2, 98, 78)], ECL_M: [(4, 49, 31)],
        ECL_Q: [(2, 32, 14), (4, 33, 15)], ECL_H: [(4, 39, 13), (1, 40, 14)]},
    8: {ECL_L: [(2, 121, 97)], ECL_M: [(2, 60, 38), (2, 61, 39)],
        ECL_Q: [(4, 40, 18), (2, 41, 19)], ECL_H: [(4, 40, 14), (2, 41, 15)]},
    9: {ECL_L: [(2, 146, 116)], ECL_M: [(3, 58, 36), (2, 59, 37)],
        ECL_Q: [(4, 36, 16), (4, 37, 17)], ECL_H: [(4, 36, 12), (4, 37, 13)]},
    10: {ECL_L: [(2, 86, 68), (2, 87, 69)], ECL_M: [(4, 69, 43), (1, 70, 44)],
         ECL_Q: [(6, 43, 19), (2, 44, 20)], ECL_H: [(6, 43, 15), (2, 44, 16)]},
}

_ALIGNMENT = {
    1: [], 2: [6, 18], 3: [6, 22], 4: [6, 26], 5: [6, 30],
    6: [6, 34], 7: [6, 22, 38], 8: [6, 24, 42], 9: [6, 26, 46], 10: [6, 28, 50],
}


# --------------------------------------------------------------------------- #
# GF(256) arithmetic, primitive polynomial x^8 + x^4 + x^3 + x^2 + 1 (0x11D)
# --------------------------------------------------------------------------- #
def _gf_mul(x: int, y: int) -> int:
    z = 0
    for i in range(7, -1, -1):
        z = (z << 1) ^ ((z >> 7) * 0x11D)
        z ^= ((y >> i) & 1) * x
    return z & 0xFF


def _rs_divisor(degree: int) -> list[int]:
    result = [0] * (degree - 1) + [1]
    root = 1
    for _ in range(degree):
        for j in range(degree):
            result[j] = _gf_mul(result[j], root)
            if j + 1 < degree:
                result[j] ^= result[j + 1]
        root = _gf_mul(root, 0x02)
    return result


def _rs_remainder(data: list[int], divisor: list[int]) -> list[int]:
    result = [0] * len(divisor)
    for b in data:
        factor = b ^ result.pop(0)
        result.append(0)
        for i, coef in enumerate(divisor):
            result[i] ^= _gf_mul(coef, factor)
    return result


def _get_bit(x: int, i: int) -> bool:
    return ((x >> i) & 1) != 0


# --------------------------------------------------------------------------- #
class QrCode:
    """A QR Code symbol built from raw byte data."""

    def __init__(self, version: int, ecl: int):
        self.version = version
        self.ecl = ecl
        self.size = version * 4 + 17
        self.modules = [[False] * self.size for _ in range(self.size)]
        self.is_function = [[False] * self.size for _ in range(self.size)]
        self._draw_function_patterns()

    # -- public API --------------------------------------------------------- #
    @staticmethod
    def encode_text(text: str, ecl: int = ECL_M, max_version: int = 10) -> "QrCode":
        data = text.encode("utf-8")
        for version in range(1, max_version + 1):
            if len(data) <= QrCode._capacity_bytes(version, ecl):
                return QrCode.encode_bytes(data, version, ecl)
        raise ValueError(
            f"data too long: {len(data)} bytes exceeds version {max_version} "
            f"capacity at this error-correction level"
        )

    @staticmethod
    def encode_bytes(data: bytes, version: int, ecl: int) -> "QrCode":
        if version not in _RS_BLOCKS:
            raise ValueError(f"unsupported version {version}")
        qr = QrCode(version, ecl)
        datacw = qr._data_codewords()
        bits: list[bool] = []

        def append(value: int, length: int) -> None:
            for i in range(length - 1, -1, -1):
                bits.append(((value >> i) & 1) != 0)

        append(0b0100, 4)  # byte mode
        append(len(data), 8 if version <= 9 else 16)
        for byte in data:
            append(byte, 8)

        capacity_bits = datacw * 8
        assert len(bits) <= capacity_bits
        append(0, min(4, capacity_bits - len(bits)))  # terminator
        append(0, (-len(bits)) % 8)                    # pad to byte boundary

        pad = 0xEC
        while len(bits) < capacity_bits:
            append(pad, 8)
            pad ^= 0xEC ^ 0x11

        codewords = [QrCode._bits_to_int(bits[i:i + 8]) for i in range(0, len(bits), 8)]
        all_codewords = qr._add_ecc_and_interleave(codewords)
        qr._draw_codewords(all_codewords)

        best_mask = qr._select_mask()
        qr._apply_mask(best_mask)
        qr._draw_format_bits(best_mask)
        return qr

    def to_rows(self) -> list[list[bool]]:
        return self.modules

    # -- capacity ----------------------------------------------------------- #
    @staticmethod
    def _capacity_bytes(version: int, ecl: int) -> int:
        datacw = sum(count * data for count, _total, data in _RS_BLOCKS[version][ecl])
        count_bits = 8 if version <= 9 else 16
        return (datacw * 8 - 4 - count_bits) // 8

    @staticmethod
    def _bits_to_int(bits: list[bool]) -> int:
        value = 0
        for bit in bits:
            value = (value << 1) | int(bit)
        return value

    def _data_codewords(self) -> int:
        return sum(count * data for count, _total, data in _RS_BLOCKS[self.version][self.ecl])

    # -- error correction --------------------------------------------------- #
    def _add_ecc_and_interleave(self, data: list[int]) -> list[int]:
        blocks = _RS_BLOCKS[self.version][self.ecl]
        num_blocks = sum(count for count, _t, _d in blocks)
        ecc_len = _RS_BLOCKS[self.version][self.ecl][0][1] - _RS_BLOCKS[self.version][self.ecl][0][2]

        data_blocks: list[list[int]] = []
        ecc_blocks: list[list[int]] = []
        k = 0
        for count, _total, datalen in blocks:
            for _ in range(count):
                block = data[k:k + datalen]
                k += datalen
                data_blocks.append(block)
                ecc_blocks.append(_rs_remainder(block, _rs_divisor(ecc_len)))
        assert k == len(data), (k, len(data))

        result: list[int] = []
        for i in range(max(len(block) for block in data_blocks)):
            for block in data_blocks:
                if i < len(block):
                    result.append(block[i])
        for i in range(ecc_len):
            for block in ecc_blocks:
                result.append(block[i])

        total = sum(count * total_cw for count, total_cw, _d in _RS_BLOCKS[self.version][self.ecl])
        assert len(result) == total, (len(result), total)
        return result

    # -- function patterns -------------------------------------------------- #
    def _set_function(self, x: int, y: int, dark: bool) -> None:
        self.modules[y][x] = dark
        self.is_function[y][x] = True

    def _draw_function_patterns(self) -> None:
        size = self.size

        # Timing patterns
        for i in range(size):
            self._set_function(6, i, i % 2 == 0)
            self._set_function(i, 6, i % 2 == 0)

        # Finder patterns + separators
        for cx, cy in ((3, 3), (size - 4, 3), (3, size - 4)):
            for dy in range(-4, 5):
                for dx in range(-4, 5):
                    x, y = cx + dx, cy + dy
                    if 0 <= x < size and 0 <= y < size:
                        dist = max(abs(dx), abs(dy))
                        self._set_function(x, y, dist != 2 and dist != 4)

        # Alignment patterns
        positions = _ALIGNMENT[self.version]
        for i, ax in enumerate(positions):
            for j, ay in enumerate(positions):
                if (i == 0 and j == 0) or (i == 0 and j == len(positions) - 1) or (
                    i == len(positions) - 1 and j == 0
                ):
                    continue
                for dy in range(-2, 3):
                    for dx in range(-2, 3):
                        self._set_function(ax + dx, ay + dy, max(abs(dx), abs(dy)) != 1)

        # Reserve format-information areas (drawn later) and the dark module
        self._draw_format_bits(0, reserve_only=True)
        self._set_function(8, size - 8, True)

        # Version information (versions 7+)
        if self.version >= 7:
            rem = self.version
            for _ in range(12):
                rem = (rem << 1) ^ ((rem >> 11) * 0x1F25)
            bits = self.version << 12 | rem
            for i in range(18):
                bit = _get_bit(bits, i)
                a = size - 11 + i % 3
                b = i // 3
                self._set_function(a, b, bit)
                self._set_function(b, a, bit)

    # -- codeword placement ------------------------------------------------- #
    def _draw_codewords(self, data: list[int]) -> None:
        bits: list[bool] = []
        for byte in data:
            for i in range(7, -1, -1):
                bits.append(((byte >> i) & 1) != 0)

        size = self.size
        i = 0
        right = size - 1
        while right >= 1:
            if right == 6:
                right = 5
            for vert in range(size):
                for j in range(2):
                    x = right - j
                    upward = ((right + 1) & 2) == 0
                    y = (size - 1 - vert) if upward else vert
                    if not self.is_function[y][x] and i < len(bits):
                        self.modules[y][x] = bits[i]
                        i += 1
            right -= 2
        assert i == len(bits), (i, len(bits))

    # -- masking ------------------------------------------------------------ #
    @staticmethod
    def _mask_bit(mask: int, x: int, y: int) -> bool:
        if mask == 0:
            return (x + y) % 2 == 0
        if mask == 1:
            return y % 2 == 0
        if mask == 2:
            return x % 3 == 0
        if mask == 3:
            return (x + y) % 3 == 0
        if mask == 4:
            return (y // 2 + x // 3) % 2 == 0
        if mask == 5:
            return (x * y) % 2 + (x * y) % 3 == 0
        if mask == 6:
            return ((x * y) % 2 + (x * y) % 3) % 2 == 0
        if mask == 7:
            return ((x + y) % 2 + (x * y) % 3) % 2 == 0
        raise ValueError(mask)

    def _apply_mask(self, mask: int) -> None:
        for y in range(self.size):
            for x in range(self.size):
                if not self.is_function[y][x] and self._mask_bit(mask, x, y):
                    self.modules[y][x] = not self.modules[y][x]

    def _select_mask(self) -> int:
        best_mask = 0
        best_penalty = None
        for mask in range(8):
            self._apply_mask(mask)
            self._draw_format_bits(mask)
            penalty = self._penalty_score()
            if best_penalty is None or penalty < best_penalty:
                best_penalty = penalty
                best_mask = mask
            self._apply_mask(mask)  # undo (XOR is self-inverse)
        return best_mask

    def _penalty_score(self) -> int:
        size = self.size
        score = 0

        # Rule 1: runs of five or more same-coloured modules
        for rows in (self.modules, list(zip(*self.modules))):
            for row in rows:
                run = 1
                for i in range(1, size):
                    if row[i] == row[i - 1]:
                        run += 1
                    else:
                        if run >= 5:
                            score += run - 2
                        run = 1
                if run >= 5:
                    score += run - 2

        # Rule 2: 2x2 blocks of the same colour
        for y in range(size - 1):
            for x in range(size - 1):
                c = self.modules[y][x]
                if c == self.modules[y][x + 1] == self.modules[y + 1][x] == self.modules[y + 1][x + 1]:
                    score += 3

        # Rule 3: finder-like 1:1:3:1:1 patterns with four light modules
        pattern_a = [True, False, True, True, True, False, True, False, False, False, False]
        pattern_b = pattern_a[::-1]
        for rows in (self.modules, list(zip(*self.modules))):
            for row in rows:
                for i in range(size - 10):
                    window = list(row[i:i + 11])
                    if window == pattern_a or window == pattern_b:
                        score += 40

        # Rule 4: deviation of the dark-module ratio from 50%
        dark = sum(sum(1 for c in row if c) for row in self.modules)
        total = size * size
        k = (abs(dark * 20 - total * 10) + total - 1) // total - 1
        score += max(k, 0) * 10
        return score

    # -- format information ------------------------------------------------- #
    def _draw_format_bits(self, mask: int, reserve_only: bool = False) -> None:
        data = (_FORMAT_ECL_BITS[self.ecl] << 3) | mask
        rem = data
        for _ in range(10):
            rem = (rem << 1) ^ ((rem >> 9) * 0x537)
        bits = (data << 10 | rem) ^ 0x5412
        size = self.size

        def place(x: int, y: int, bit: bool) -> None:
            if reserve_only:
                self.is_function[y][x] = True
            else:
                self.modules[y][x] = bit

        for i in range(6):
            place(8, i, _get_bit(bits, i))
        place(8, 7, _get_bit(bits, 6))
        place(8, 8, _get_bit(bits, 7))
        place(7, 8, _get_bit(bits, 8))
        for i in range(9, 15):
            place(14 - i, 8, _get_bit(bits, i))

        for i in range(8):
            place(size - 1 - i, 8, _get_bit(bits, i))
        for i in range(8, 15):
            place(8, size - 15 + i, _get_bit(bits, i))
