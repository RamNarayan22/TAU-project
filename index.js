const express=require('express');
const app = express();
const fs=require('fs');
const path = require('path');
app.set("view engine","ejs")
app.set(express.static(path.join(__dirname,'public')))
app.set(express.json())

app.set(express.urlencoded({extended:true}))
app.get('/',function(req,res){
    fs.readdir(`./files`,function(err,files){
        res.render('index',{files:files})
        

    })
})    
app.post('/create',function(req,res){

    fs.writeFile(`./files/${req.body.tit.split(' ').join("")}.txt`, req.body.detail ,function(err){
    

        
        res.redirect('/')
        
    
        })
    

    
})
app.listen(3000)