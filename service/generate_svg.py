import subprocess

from service.utils.get_tmp_data_path import get_request_tmp_path
from service.utils.settings import get_setting


def generate_svg(data, file_id, files):
    output_prefix = f"{get_request_tmp_path(file_id)}/reviewer"
    locus = data.get("locus", "")

    cmd = [
        get_setting("REV_PATH"),
        "--reads",
        files.get("reads", ""),
        "--vcf",
        files.get("vcf", ""),
        "--catalog",
        files.get("catalog") or get_setting("REV_CATALOG_PATH"),
        "--locus",
        locus,
        "--reference",
        data.get("reference") or get_setting("REV_REF_PATH"),
        "--output-prefix",
        output_prefix,
    ]

    result = subprocess.run(cmd, stdout=subprocess.PIPE, check=True)

    print("REViewer:")
    print(result.stdout.decode("utf-8"))

    return f"{output_prefix}.{locus}.svg"


def generate_trgt_svg(data, file_id, files):
    locus = data.get("locus", "")
    output_file = f"{get_request_tmp_path(file_id)}/trgt.svg"

    cmd = [
        get_setting("TRGT_PATH"),
        "plot",
        "--spanning-reads",
        files.get("reads", ""),
        "--vcf",
        files.get("vcf", ""),
        "--repeats",
        files.get("catalog") or get_setting("TRGT_CATALOG_PATH"),
        "--repeat-id",
        locus,
        "--genome",
        data.get("reference") or get_setting("TRGT_REF_PATH"),
        "--image",
        output_file,
        "--plot-type",
        data.get("plot_type", "allele"),
        "--show",
        data.get("show", "motifs"),
    ]
    if data.get("squished"):
        cmd.append("--squished")

    result = subprocess.run(cmd, stdout=subprocess.PIPE, check=True)

    print("trgt:")
    print(result.stdout.decode("utf-8"))

    return f"{output_file}"
