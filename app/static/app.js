document.addEventListener('DOMContentLoaded', ()=>{
  const editor = document.getElementById('editor')
  const title = document.getElementById('title')
  const sideList = document.getElementById('side-list')

  document.getElementById('add-headline').addEventListener('click', ()=>{
    const sel = window.getSelection()
    if(sel && sel.rangeCount){
      const range = sel.getRangeAt(0)
      const h = document.createElement('h2')
      h.textContent = range.toString() || 'Headline'
      range.deleteContents()
      range.insertNode(h)
    } else {
      const h = document.createElement('h2')
      h.textContent = 'Headline'
      editor.appendChild(h)
    }
  })

  function wrapSelection(className){
    const sel = window.getSelection()
    if(!sel || !sel.rangeCount) return
    const range = sel.getRangeAt(0)
    const span = document.createElement('span')
    span.className = className
    span.appendChild(range.extractContents())
    range.insertNode(span)
    sel.removeAllRanges()
  }

  document.getElementById('highlight').addEventListener('click', ()=>wrapSelection('highlight'))
  document.getElementById('circle').addEventListener('click', ()=>wrapSelection('circle'))

  document.getElementById('side-note').addEventListener('click', ()=>{
    const text = prompt('Write a quick side note:')
    if(!text) return
    const li = document.createElement('li')
    li.textContent = text
    sideList.appendChild(li)
  })

  document.getElementById('save').addEventListener('click', async ()=>{
    const payload = {
      title: title.value || 'Untitled',
      content: editor.innerHTML,
      side_notes: Array.from(sideList.querySelectorAll('li')).map(li => li.textContent)
    }
    const res = await fetch('/api/notes', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)})
    if(res.ok){
      const data = await res.json()
      alert('Saved: ' + data.id)
    } else {
      alert('Save failed')
    }
  })

  // Load first existing note for demo
  fetch('/api/notes').then(r=>r.json()).then(list=>{
    if(list && list.length){
      const n = list[0]
      title.value = n.title
      editor.innerHTML = n.content
      sideList.innerHTML = ''
      (n.side_notes||[]).forEach(s=>{const li=document.createElement('li');li.textContent=s;sideList.appendChild(li)})
    }
  })
})
