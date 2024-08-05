from dataclasses import dataclass, field
from typing import List, Optional
import random
from markdown import markdown

from fasthtml.common import *

css = Style('''
body { max-width:600px; }

ul {
  list-style-type: none;
  padding-inline-start: 20px;
}

.chk-icon { font-size: 14px; }
.chk-icon.bi-check-square-fill { color: #00f; }

.itm {
  display: grid;
  grid-template-columns: 20px auto;
  grid-template-rows: 20px auto auto;
  grid-template-areas:
    "checkbox content"
    "none content"
    "none subline";;
  align-items: start;
}

.itm_chkbox { grid-area: checkbox; }

.itm_content p             { margin: 5px 0; }
.itm_content p:first-child { margin-top: 0; }
.itm_content p:last-child  { margin-bottom: 0; }
''')
icons = Link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css")

app, rt = fast_app(pico=False, live=True, hdrs=(icons, css,))

@dataclass
class Itm:
  id: str
  content: str
  parent: str = ""
  checked: bool = False
  edit: bool= False

  def content_display(self):
    if self.edit:
      components = []
      components.append(
        Form(
          Textarea(self.content, name="_content"),
          Br(),
          Button(
            "Submit",
            hx_target = f"#{self.component_id}",
            hx_post= f"/update/content/{self.id}",
            hx_swap="outerHTML",
          )
        )
      )

      return Div(
        *components,
        style="grid-area: content;"
      )
    else:
      return Div(
        NotStr(
          markdown(self.content, output_format="html5"),
        ),
        hx_target=f"#{self.component_id}",
        hx_get=f"/update/edit/{self.id}",
        hx_swap="outerHTML",
        style="grid-area: content;",
        cls="itm_content",
      )

  def check_box(self):
    type_cls = "bi bi-check-square-fill" if self.checked else "bi bi-square"
    return Div(
      I(
        cls="chk-icon "+type_cls,
        hx_target = f"#{self.component_id}",
        hx_get = f"/update/checked/{self.id}",
        hx_swap="outerHTML",
      ),
      cls="itm_chkbox"
    )

  @property
  def component_id(self):
    return f"itm_{self.id}"

  def __ft__(self):
    return Div(
      self.check_box(),
      self.content_display(),
      id = self.component_id,
      cls = "itm"
    )

@dataclass
class Node:
  itm: Itm
  children: List['Node'] = field(default_factory=list)

  def __ft__(self):
    components = [self.itm]
    if self.children:
      components.append(
        Ul(*[child for child in self.children])
      )
    return Li(*components)

  def __str__(self):
    task_ids = [child.itm.id for child in self.children if child]
    return f"Node({self.itm.id}, children=[{task_ids}])"

  def __repr__(self):
    return self.__str__()


@rt('/')
def get():
  return Ul(*ROOT.children)

@rt('/update/checked/{itm_id}')
def get(itm_id:str):
  if itm_id in DATA:
    DATA[itm_id].checked = not DATA[itm_id].checked
    return DATA[itm_id]
  return None

@rt('/update/edit/{itm_id}')
def get(itm_id:str):
  if itm_id in DATA:
    DATA[itm_id].edit = not DATA[itm_id].edit
    return DATA[itm_id]
  return None

@rt('/update/content/{itm_id}')
async def post(itm_id:str, request: Request):
  data = form2dict(await request.form())
  if itm_id in DATA:
    DATA[itm_id].content = data['_content']
    DATA[itm_id].edit = False
    return DATA[itm_id]
  return None

DATA = {}
parent_id = [0]*50
with open("test.md") as F:
  for idx, line in enumerate(F.readlines(),start=1):
    indent = line.find('- [')
    parent_id[indent//2+1] = idx
    itm = Itm(
      id = str(idx),
      content = line[indent+6:-1],
      parent = str(parent_id[indent//2]),
      checked = line[indent+3]=="x"
    )
    DATA[str(idx)] = itm

ROOT = Node(Itm("0",""))

def add_subtasks(node):
  for itm_id, datum in DATA.items():
    if datum.parent == node.itm.id:
      new_node = Node(datum)
      node.children.append(new_node)
      add_subtasks(new_node)

add_subtasks(ROOT)

serve()

