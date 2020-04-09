var str=""
let images = document.querySelectorAll('img')
var imagesloaded = []
for (var i = 0; i < images.length; i++) {
  imagesloaded.push(false)
}
var myVar = setInterval(sequenceLoad, 1000)

function lazyLoad () {
  for(let i = 0; i < images.length; i++) {
    if (imagesloaded[i]) {
        continue
    }
    let image = images[i]
    if (getElementTop(image) <= window.innerHeight + document.documentElement.scrollTop) {
      image.src = image.getAttribute('data-src')
      imagesloaded[i] = true
      str = str+i+","
      document.getElementById("demo").innerHTML = str;
    }
  }
}

function getElementTop (element) {
  let actualTop = element.offsetTop
  let parent = element.offsetParent

  while (parent !== null) {
    actualTop += parent.offsetTop
    parent = parent.offsetParent
  }

  return actualTop
}

function sequenceLoad() {
  var allLoaded = true
  for(let i = 0; i < images.length; i++) {
    if (!imagesloaded[i]) {
        allLoaded = false
        let image = images[i]
        image.src = image.getAttribute('data-src')
        imagesloaded[i] = true
        document.getElementById("demo").innerHTML = "loading..." + i
        break
    }
  }
  if (allLoaded) {
    document.getElementById("demo").innerHTML = "loading complete"
    clearInterval(myVar)
  }
}

sequenceLoad()

//lazyLoad()
//window.onscroll = lazyLoad
