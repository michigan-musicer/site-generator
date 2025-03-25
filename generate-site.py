import os
from sys import stderr, stdout, stdin

MARKDOWN_FOLDER = os.path.join(os.getcwd(), 'markdown')
OUT_FOLDER = os.path.join(os.getcwd(), 'content')

class engine:

  def __init__(self):
    self.filename = None
    self.outfile = None
    self.lines = None
    self.line_number = None
    self.sidenote_id = 0
    
  def m_reset(self):
    self.line_number = 0
    self.sidenote_id = 0
  
  def m_increment_sidenote_id(self):
    self.sidenote_id += 1

  def m_done(self):
    return self.line_number == len(self.lines)

  def m_readline(self):
    line = self.lines[self.line_number]
    self.line_number += 1
    return line
  
  # find pairs of 
  def m_processline(self, line):
    while line.find('**') != -1:
      line = line.replace('**', '<b>', 1)
      if line.find('**') == -1:
        stderr.write('opening ** missing closing **')
        exit(1)
      line = line.replace('**', '</b>', 1)
    while line.find('*') != -1:
      line = line.replace('*', '<em>', 1)
      if line.find('*') == -1:
        stderr.write('opening * missing closing *')
        exit(1)
      line = line.replace('*', '</em>', 1)
    # sidenotes
    while line.find('^^') != -1:
      start = line.find('^^')
      end = line.find('^^', start + 1)
      if end == -1:
        stderr.write('opening ** missing closing ^^')
        exit(1)
      sidenote_id = f"sn-{str(self.sidenote_id)}"
      sidenote = f'<label for="{sidenote_id}" class="margin-toggle sidenote-number"></label>' + \
                 f'<input type="checkbox" id="{sidenote_id}" class="margin-toggle">' + \
                 f'<span class="sidenote">{line[start + 2:end]}</span>'
      line = line[:start] + sidenote + line[end + 2:]

      self.m_increment_sidenote_id()
    return line

  def parse_frontmatter(self):
    if self.lines[self.line_number] != '---':
      stderr.write(f'{self.filename} has no frontmatter, not parsing frontmatter\n')
      return None
    
    frontmatter = {}
    self.m_readline()
    while self.lines[self.line_number] != '---':
      line = self.m_readline()
      key, value = line.split(': ')[0], line.split(': ')[1]
      frontmatter[key] = value.strip('"')
    
    self.m_readline()
    return frontmatter

  def main(self):
    for file in os.listdir(MARKDOWN_FOLDER):
      self.m_reset()

      self.filename = os.path.join(MARKDOWN_FOLDER, file)
      outfile = os.path.join(OUT_FOLDER, file.replace('.md', '.html'))
      if not self.filename.endswith('.md'):
        stderr.write(f'{self.filename} is not a markdown file, continuing\n')
        continue
      
      with open(self.filename, 'r') as f, open(outfile, 'w') as out:
        self.lines = f.read().splitlines()
        if len(self.lines) == 0:
          stderr.write(f'{self.filename} is empty, continuing\n')
          continue

        
        frontmatter = self.parse_frontmatter()
        
        out.write('<html lang="en">\n')
        out.write('<head>\n')
        if frontmatter:
          out.write(f'<title>{frontmatter["title"]} | Title of the book</title>\n')
        out.write('<meta name="viewport" content="width=device-width, initial-scale=1"/>')
        out.write('<link rel="stylesheet" type="text/css" href="style.css"/>\n')
        out.write('<link href="https://fonts.googleapis.com/css?family=Source+Code+Pro:400|Source+Sans+Pro:300,400,600" rel="stylesheet" type="text/css">\n')
        out.write('</head>\n')
        # print((self.lines, self.line_number))
        out.write('<body>\n')
        # NOTE: let's pretend for now we have a table of contents that goes
        # - Introduction 
        # - Way of Working
        # - Industry track
        # - Grad school track
        # - Miscellaneous
        # and hardcode this into the script that writes this to outfile.
        # It may be better to separate this out later (esp to add chapters, but let's not overneigneer like always lol).
        # out.write('<div class="navigation">\n')
        # out.write('<ol>\n')
        # out.write('<li>Introduction</li>\n')
        # out.write('<li>Way of Working</li>\n')
        # out.write('<li>Industry Track</li>\n')
        # out.write('<li>Graduate School Track</li>\n')
        # out.write('<li>Miscellaneous</li>\n')
        # out.write('</ol>\n')
        # out.write('</div>\n')
        
        out.write('<div class="main">')
        
        out.write(f'<h1>{frontmatter["title"]}</h1>')
        out.write('<hr/>')
        
        in_ul = False
        while not self.m_done():
          line = self.m_readline()
          if not line:
            continue
          if in_ul and not line.startswith('-'):
             out.write(f'</ul>\n')
          
          # this needs to be cased for other headings, maybe
          if line.startswith('#'):
            if line.startswith('####'):
              line = line[line.find('####') + 4:].strip()
              out.write(f'<h4>{self.m_processline(line)}</h4>\n')
            elif line.startswith('###'):
              line = line[line.find('###') + 3:].strip()
              out.write(f'<h3>{self.m_processline(line)}</h3>\n')
            elif line.startswith('##'):
              line = line[line.find('##') + 2:].strip()
              out.write(f'<h2>{self.m_processline(line)}</h2>\n')
            elif line.startswith('#'):
              line = line[line.find('#') + 1:].strip()
              out.write(f'<h1>{self.m_processline(line)}</h1>\n')
            else:
              # This is obviously dumb if it's just that we want h5 or h6,
              # but it's more meaningful if it's some other error
              stderr.write(f'Could not write {self.m_processline(line)}')
              continue
          elif line.startswith('-'):
            if not in_ul:
              in_ul = True 
              out.write(f'<ul>\n')
            line = line[line.find('-') + 1:].strip()
            out.write(f'<li>{self.m_processline(line)}</li>\n')
          
          elif line.startswith('>'):
            line = line[line.find(':') + 1:].strip()
            out.write(f'<blockquote>{self.m_processline(line)}</blockquote>\n')
          elif line.startswith('{'):
            if line.startswith('{caveat}:'):
              line = line[line.find(':') + 1:].strip()
              out.write(f'<div class="caveat">\n<h3>CAVEAT</h3><p>{self.m_processline(line)}</p>\n')
            elif line.startswith('{/caveat}'):
              out.write('</div>\n')
            elif line.startswith('{value}:'):
              line = line[line.find(':') + 1:].strip()
              out.write(f'<div class="value">\n<h3>VALUE JUDGEMENT</h3><p>{self.m_processline(line)}</p>\n')
            elif line.startswith('{/value}'):
              out.write('</div>\n')
            elif line.startswith('{caution}:'):
              line = line[line.find(':') + 1:].strip()
              out.write(f'<div class="caution">\n<h3>A WORD OF CAUTION</h3><p>{self.m_processline(line)}</p>\n')
            elif line.startswith('{/caution}'):
              out.write('</div>\n')
            elif line.startswith('{unqualified}:'):
              line = line[line.find(':') + 1:].strip()
              out.write(f'<div class="unqualified">\n<h3>WHERE I&apos;M NOT QUALIFIED</h3><p>{self.m_processline(line)}</p>\n')
            elif line.startswith('{/unqualified}'):
              out.write('</div>\n')
            elif line.startswith('{numbers}:'):
              line = line[line.find(':') + 1:].strip()
              out.write(f'<div class="numbers">\n<h3>BY THE NUMBERS</h3><p>{self.m_processline(line)}</p>\n')
            elif line.startswith('{/numbers}'):
              out.write('</div>\n')
            elif line.startswith('{TODO}:'):
              line = line[line.find(':') + 1:].strip()
              out.write(f'<div class="TODO">\n<h3>TODO</h3><p>{self.m_processline(line)}</p>\n')
            elif line.startswith('{/TODO}'):
              out.write('</div>\n')
          else:
            out.write(f'<p>{self.m_processline(line)}</p>\n')
        
        out.write('</div>') # /main
        
        out.write('</body>\n')
        out.write('</html>\n')
          

if __name__ == '__main__':
  e = engine()
  e.main()
