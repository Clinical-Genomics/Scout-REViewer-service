import asyncio
import async_timeout
import json
from aiohttp import ClientSession
from flask import Flask, request, jsonify
from flask_expects_json import expects_json
from flask_expects_json import expects_json
from service.request_data import get_all_urls

app = Flask(__name__)

schema = {
    'type': 'object',
    'properties': {
        # --reads <BAMlet generated by ExpansionHunter> \
        'reads': {'type': 'string'},
        # --vcf <VCF file generated by ExpansionHunter> \
        'vcf': {'type': 'string'},
        # --reference <FASTA file with reference genome> \
        # 'reference': {'type': 'string'},
        # --catalog <Variant catalog> \
        'catalog': {'type': 'string'},
        # --locus <Locus to analyze> \
        'locus': {'type': 'string'},
        # --output-prefix <Prefix for the output files>
        # 'output-prefix': {'type': 'string'},
    },
    'required': ['reads', 'vcf', 'locus']
}

@app.route('/')
def home():
    return 'REViewer service is running!!!'

@app.route('/reviewer', methods=['POST'])
# @expects_json(schema)
async def create_task():
    # parse path of files to use with REViewer
    request_data = request.get_json()
    urls = [
      request_data.get('reads', ''),
      request_data.get('vcf', ''),
      request_data.get('catalog', '')
      # request_data.get('locus')
    ]

    # TODO: get files from remote
    # TODO: store files from remote
    # TODO: run REViewer with local file path as arguments
    # TODO: send back REViewer generated SVG

    results = await get_all_urls(urls)

    print(results)

    with open("./tmp_data/test.txt", "w") as fo:
       fo.write("This is Test Data")

    return f'''<svg
      version="1.1"
       baseProfile="full"
       width="800" height="100"
       xmlns="http://www.w3.org/2000/svg">

      <rect width="100%" height="100%" fill="red" />
      <text x="20" y="30" font-size="20" fill="black">
        Reads: {request_data.get('reads', '')}
      </text>
      <text x="20" y="50" font-size="20" fill="black">
        VCF: {request_data.get('vcf', '')}
      </text>
      <text x="20" y="70" font-size="20" fill="black">
        Catalog: {request_data.get('catalog', '')}
      </text>
      <text x="20" y="90" font-size="20" fill="black">
        Locus: {request_data.get('locus', '')}
      </text>
    </svg>'''

