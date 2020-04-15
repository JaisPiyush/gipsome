from bs4 import BeautifulSoup
from bs4.element import Tag
class Engine:

    def parser(self,data,page_name="index"):
        """
          {"tag","attributes","closed","childrens"}
        """
        data = data.rstrip("\n")
        self.soup = BeautifulSoup(data,features='html.parser')
        self.parsed= self.convert(self.soup.html)
        return {page_name:self.parsed}
    
    def convert(self,tag):
        if isinstance(tag,Tag):
            converted = {
                "tag":f"{tag.name}",
                "attributes":tag.attrs,
                "closed": 0 if tag.can_be_empty_element else 1,
                "childrens":[]
            }
            if not tag.can_be_empty_element:
                for child in tag.childGenerator():
                    converted["childrens"].append(self.convert(child))
                return converted
            else:
                return converted
        else:
            return tag


    def render(self, data,page_name='index'):
        """
         stored as {"page_name":[{}]}
         data = {"tag":"html","attributes","childrens"}
         json : {"tag":"","attributes":{},"closed":1/0,"childrens":[]}
        """
        # data = json.locleads(data)
        self.template = ""
        self.template = self.template + self.node_render(data[page_name])
        return self.template

    def node_render(self, node):
        template = f"<{node['tag']}"
        if 'attributes' in node.keys():
            # print(node['attributes'].keys())
            for key in node['attributes'].keys():
                value = node['attributes'][key]
                # print(value)
                template = template + f' {key} = "{value}"'
        if node['closed'] == 1:
            template = template + ">\n"
        else:
            template = template + " />\n"
        if 'childrens' in node.keys() and node['childrens'] is not []:
            for value in node['childrens']:
                if isinstance(value, str):
                    # print(value)
                    template = template + f"{value}"
                else:
                    template = template + self.node_render(value)
        if node['closed'] == 1:
            template = template + f"</{node['tag']}>"

        return template



# data = '''
# <html lang="en" >
# <head lang="en">
# <title>Title</title>
# <script>var a = 12;
# console.log(a);
# </script></head>
# <body>
# <img src="abc" />
# <p class = "color: red;"> Name</p>
# <p>norm</p></body></html>
# '''

# engine = Engine()
# parsed = engine.parser(data)
# print(parsed)
# print(engine.render(parsed))