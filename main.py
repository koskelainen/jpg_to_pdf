import logging
from argparse import ArgumentParser, RawTextHelpFormatter
from os import remove
from re import search, findall
from typing import List, Tuple

from PIL import Image
from fpdf import FPDF
from pathlib3x import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


def get_files(root_path: Path, regex: str) -> List[Tuple[int, Path]]:
    image_list = []
    for jpg_file in Path(root_path).iterdir():
        if search(regex, jpg_file.as_posix()) is None:
            continue
        result = findall(r"\d+", jpg_file.as_posix())
        num_jpeg, *_ = result[::-1] if result else [None]
        if not num_jpeg:
            logging.warning(f"skip file '{jpg_file}', because name not contain digits")
            continue
        image_list.append((int(num_jpeg), jpg_file))
    image_list.sort(key=lambda x: x[0])
    logging.info(f"found {len(image_list)} image files.")
    return image_list


def rotate_and_landscape_mode_image(image_list: List[Tuple[int, Path]]) -> None:
    count = 0
    if not image_list:
        return
    for idx, fpath in image_list:
        im1 = Image.open(fpath.as_posix())
        width, height = im1.size
        if width > height:
            im2 = im1.transpose(Image.ROTATE_270)
            remove(fpath.as_posix())
            im2.save(fpath.as_posix())
            count += 1
    logging.info(f"number of rotated images {count}")


def convert_to_pdf(image_list: List[Tuple[int, Path]], pdf_file: Path) -> None:
    if not image_list:
        return

    pdf = FPDF()
    for idx, fpath in image_list:
        logging.info(f"add file '{fpath}'")
        pdf.add_page()
        # 210 and 297 are the dimensions of an A4 size sheet.
        pdf.image(fpath.as_posix(), 0, 0, 210, 297)
    pdf.output(**dict(name=pdf_file.as_posix(), dest="F"))

    if not pdf_file.exists():
        logging.error(f"fail generate file: '{pdf_file}'")
    logging.info(f"pdf generated successfully: '{pdf_file}'")


if __name__ == "__main__":
    pattern = r".*(jpe?g|png)"
    parser = ArgumentParser(
        prog=f"Script to convert {pattern} files to pdf",
        description=f"Search {pattern} files from the directory.\n"
                    f"Named files must contain digits for order append to pdf.\n"
                    f"Result pdf file: <path to folder>.pdf",
        epilog=f"For example: python {Path(__file__).name} -d ./images",
        formatter_class=RawTextHelpFormatter
    )
    parser.add_argument("-d", "--dir", type=str,
                        help="directory with images")
    args = parser.parse_args()
    if args.dir is None:
        parser.print_help()
        exit(1)
    root_dir = Path(args.dir).absolute()
    pdf_result = Path(f"{root_dir}.pdf")

    main_image_list = get_files(root_path=root_dir, regex=pattern)
    rotate_and_landscape_mode_image(main_image_list)
    convert_to_pdf(main_image_list, pdf_file=pdf_result)
