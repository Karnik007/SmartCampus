import os
import re

search_dir = r'C:\Users\hp\Desktop\AMDProject\backend\templates'
pattern = re.compile(r'\s*<script>\s*\{\%\s*if\s*user\.is_authenticated\s*\%\}.*?\{\%\s*endif\s*\%\}\s*</script>', re.DOTALL)

replacement = '''
    <!-- User Data for JS -->
    {% if user.is_authenticated %}
    <script type="application/json" id="user-data">
        {"name": "{{ user.first_name|default:user.email|escapejs }}", "email": "{{ user.email|escapejs }}", "id": {{ user.id }}, "provider": "email"}
    </script>
    {% endif %}

    <script>
        // Parse user data safely to avoid IDE lint errors
        var userDataEl = document.getElementById('user-data');
        if (userDataEl) {
            if (!localStorage.getItem('smartcampus-user')) {
                try {
                    var data = JSON.parse(userDataEl.textContent);
                    localStorage.setItem('smartcampus-user', JSON.stringify(data));
                } catch(e) {}
            }
        } else {
            localStorage.removeItem('smartcampus-user');
        }
    </script>'''

modified = 0
for root, _, files in os.walk(search_dir):
    for f in files:
        if f.endswith('.html'):
            filepath = os.path.join(root, f)
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()
            
            if pattern.search(content):
                new_content = pattern.sub(replacement, content)
                with open(filepath, 'w', encoding='utf-8') as file:
                    file.write(new_content)
                modified += 1
                print(f'Updated {filepath}')

print(f'Total files modified: {modified}')
