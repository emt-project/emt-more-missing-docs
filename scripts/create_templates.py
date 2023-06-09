import glob
import jinja2
import os
from acdh_tei_pyutils.tei import TeiReader
from datetime import date
from slugify import slugify
import lxml.etree as ET

out_dir = "editions"
os.makedirs(out_dir, exist_ok=True)
templateLoader = jinja2.FileSystemLoader(searchpath="./scripts/templates")
templateEnv = jinja2.Environment(loader=templateLoader)
template = templateEnv.get_template("tei_template.xml")

print("collect image infos")
mets = glob.glob("./mets/*/*_name.xml")
nsmap = {"mets": "http://www.loc.gov/METS/", "xlink": "http://www.w3.org/1999/xlink"}

img_map = {}
for x in mets:
    print(x)
    parts = os.path.split(x)
    col_id = parts[0].replace("./mets/", "")
    doc_id = parts[1].split("_")[0]
    item = {"doc_id": doc_id, "col_id": col_id}
    mets_file = x.replace("image_name", "mets")
    mets_doc = TeiReader(mets_file)
    item["images"] = []
    for y in mets_doc.tree.xpath(
        './/mets:fileGrp[@ID="IMG"]//mets:file/mets:FLocat/@xlink:href',
        namespaces=nsmap,
    ):
        item["images"].append(y)
    img_doc = TeiReader(x)
    item["img_file_names"] = img_doc.any_xpath(".//item/text()")
    img_map[doc_id] = item

files = glob.glob("./alltei/*.xml")

for x in files:
    item = {}
    item["current_date"] = f"{date.today()}"
    heads, tail = os.path.split(x)
    doc_id = tail.replace("_tei.xml", "")

    item["doc_id"] = doc_id
    item["col_id"] = img_map[doc_id]["col_id"]
    try:
        doc = TeiReader(x)
    except Exception as e:
        print(doc_id, e)
        continue
    title = doc.any_xpath('.//tei:title[@type="main"]/text()')[0]
    item["title"] = f"FIX ME: {title} "
    item["sender"] = "Eleonora Magdalena von Pfalz-Neuburg"
    item["sender_id"] = "emt_person_id__9"
    file_name = f"{slugify(title)}.xml"
    item["file_name"] = file_name
    save_path = os.path.join(out_dir, file_name)
    for i, pb in enumerate(doc.any_xpath(".//tei:graphic")):
        same_as = img_map[doc_id]["img_file_names"][i]
        pb.attrib["url"] = same_as
    facsimile = doc.any_xpath(".//tei:facsimile")[0]
    item["facsimile"] = (
        ET.tostring(facsimile, encoding="utf-8", pretty_print=True)
        .decode("utf-8")
        .replace(' xmlns="http://www.tei-c.org/ns/1.0"', "")
    )
    for i, pb in enumerate(doc.any_xpath(".//tei:pb")):
        same_as = img_map[doc_id]["images"][i]
        pb.attrib["source"] = same_as
        pb.attrib["id"] = f'{img_map[doc_id]["img_file_names"][i]}'
    body = doc.any_xpath(".//tei:body")[0]
    body_string = ET.tostring(body, encoding="utf-8", pretty_print=True).decode("utf-8")
    body_string = body_string.replace(' xmlns="http://www.tei-c.org/ns/1.0"', "")
    body_string = body_string.replace('reason=""', "")
    body_string = body_string.replace('type=""', "")
    body_string = body_string.replace("<blackening>", '<seg type="blackening">')
    body_string = body_string.replace("</blackening>", "</seg>")
    body_string = body_string.replace("<comment>", '<seg type="comment">')
    body_string = body_string.replace("</comment>", "</seg>")
    body_string = body_string.replace("<blackening/>", "")
    body_string = body_string.replace("<comment/>", "")
    item["body_string"] = body_string
    with open(save_path.lower(), "w") as f:
        f.write(template.render(**item))

for x in glob.glob(f"{out_dir}/*.xml"):
    doc = TeiReader(x)