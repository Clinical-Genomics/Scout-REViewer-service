import subprocess

from dotenv import dotenv_values

from service.utils.get_tmp_data_path import get_request_tmp_path


def generate_svg(data, file_id, files):
    env = dotenv_values(".env")
    output_prefix = f"{get_request_tmp_path(file_id)}/reviewer"
    locus = data.get("locus", "")

    cmd = [
        env.get("REV_PATH"),
        "--reads",
        files.get("reads", ""),
        "--vcf",
        files.get("vcf", ""),
        "--catalog",
        files.get("catalog") or env.get("REV_CATALOG_PATH"),
        "--locus",
        locus,
        "--reference",
        data.get("reference") or env.get("REV_REF_PATH"),
        "--output-prefix",
        output_prefix,
    ]

    result = subprocess.run(cmd, stdout=subprocess.PIPE, check=True)

    print("REViewer:")
    print(result.stdout.decode("utf-8"))

    return f"{output_prefix}.{locus}.svg"


def generate_trgt_svg(data, file_id, files):
    env = dotenv_values(".env")
    locus = data.get("locus", "")
    output_file = f"{get_request_tmp_path(file_id)}/{locus}.svg"

    cmd = [
        env.get("TRGT_PATH"),
        "plot",
        "--spanning-reads",
        files.get("reads", ""),
        "--vcf",
        files.get("vcf", ""),
        "--repeats",
        files.get("catalog") or env.get("TRGT_CATALOG_PATH"),
        "--repeat-id",
        locus,
        "--genome",
        data.get("reference") or env.get("TRGT_REF_PATH"),
        "--image",
        output_file,
    ]

    result = subprocess.run(cmd, stdout=subprocess.PIPE, check=True)

    print("trgt:")
    print(result.stdout.decode("utf-8"))

    return f"{output_file}"
