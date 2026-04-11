import { useState, useEffect, useRef, useMemo } from "react";

// \u2500\u2500\u2500 ADMIN PASSWORD \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
const ADMIN_PASS = "RajAdmin@2024";

// \u2500\u2500\u2500 INITIAL CATEGORIES \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
const INIT_CATEGORIES = [
  { id: "cold-drinks", name: "Cold Drinks", icon: "\ud83e\udd64", color: "#e8f4fd" },
  { id: "cakes", name: "Cakes", icon: "\ud83c\udf82", color: "#fff0f5" },
  { id: "namkeen", name: "Namkeen", icon: "\ud83e\udd5c", color: "#fffbea" },
  { id: "chips", name: "Chips & Snacks", icon: "\ud83c\udf5f", color: "#fff5e6" },
  { id: "biscuits", name: "Biscuits", icon: "\ud83c\udf6a", color: "#fdf5e6" },
  { id: "ice-cream", name: "Ice Creams", icon: "\ud83c\udf66", color: "#f0fff4" },
  { id: "tobacco", name: "Tobacco & Cigarettes", icon: "\ud83d\udeac", color: "#f5f5f5", optional: true },
];

// \u2500\u2500\u2500 INITIAL PRODUCTS \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
const INIT_PRODUCTS = [
  // Cold Drinks
  { id:"p001", name:"Sting Energy Drink", category:"cold-drinks", brand:"Sting", price:20, discountPrice:null, stock:"In Stock", quantity:50, image:"https://images.unsplash.com/photo-1625772299848-391b6a87d7b3?w=400&q=80", description:"Energizing carbonated drink with power-packed taste", tags:["drink","energy","cold"], status:"active" },
  { id:"p002", name:"Coca Cola 600ml", category:"cold-drinks", brand:"Coca Cola", price:40, discountPrice:35, stock:"In Stock", quantity:30, image:"https://images.unsplash.com/photo-1554866585-cd94860890b7?w=400&q=80", description:"Classic refreshing cola drink", tags:["cold drink","cola"], status:"active" },
  { id:"p003", name:"Sprite 250ml", category:"cold-drinks", brand:"Sprite", price:20, discountPrice:null, stock:"In Stock", quantity:40, image:"https://images.unsplash.com/photo-1625772299848-391b6a87d7b3?w=400&q=80", description:"Crisp lemon-lime carbonated drink", tags:["sprite","lime","cold"], status:"active" },
  { id:"p004", name:"Frooti Mango 200ml", category:"cold-drinks", brand:"Frooti", price:15, discountPrice:null, stock:"In Stock", quantity:60, image:"https://images.unsplash.com/photo-1571091718767-18b5b1457add?w=400&q=80", description:"Fresh mango fruit drink", tags:["mango","frooti","juice"], status:"active" },
  { id:"p005", name:"Red Bull 250ml", category:"cold-drinks", brand:"Red Bull", price:115, discountPrice:110, stock:"In Stock", quantity:20, image:"https://images.unsplash.com/photo-1622543925917-763c34d1a86e?w=400&q=80", description:"Premium energy drink with taurine & caffeine", tags:["energy","redbull","premium"], status:"active" },
  { id:"p006", name:"Tropicana Orange 1L", category:"cold-drinks", brand:"Tropicana", price:90, discountPrice:80, stock:"In Stock", quantity:25, image:"https://images.unsplash.com/photo-1621506289937-a8e4df240d0b?w=400&q=80", description:"100% real fruit juice", tags:["juice","orange","health"], status:"active" },

  // Cakes
  { id:"p007", name:"Chocolate Cake (1kg)", category:"cakes", brand:"Raj Confectionery", price:450, discountPrice:400, stock:"In Stock", quantity:10, image:"https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=400&q=80", description:"Rich dark chocolate layered cake with cream frosting", tags:["chocolate","cake","birthday"], status:"active" },
  { id:"p008", name:"Butterscotch Cake (1kg)", category:"cakes", brand:"Raj Confectionery", price:420, discountPrice:380, stock:"In Stock", quantity:8, image:"https://images.unsplash.com/photo-1464349095431-e9a21285b5f3?w=400&q=80", description:"Creamy butterscotch cake with caramel drizzle", tags:["butterscotch","cake","sweet"], status:"active" },
  { id:"p009", name:"Black Forest Cake (1kg)", category:"cakes", brand:"Raj Confectionery", price:500, discountPrice:450, stock:"In Stock", quantity:6, image:"https://images.unsplash.com/photo-1565808229224-264b2d4c1397?w=400&q=80", description:"Classic German-style chocolate cherry cake", tags:["black forest","cherry","cake"], status:"active" },
  { id:"p010", name:"Red Velvet Cake (1kg)", category:"cakes", brand:"Raj Confectionery", price:550, discountPrice:500, stock:"In Stock", quantity:5, image:"https://images.unsplash.com/photo-1586788680434-30d324b2d46f?w=400&q=80", description:"Velvety red sponge with cream cheese frosting", tags:["red velvet","cream","premium"], status:"active" },
  { id:"p011", name:"Pineapple Cake (1kg)", category:"cakes", brand:"Raj Confectionery", price:400, discountPrice:350, stock:"In Stock", quantity:12, image:"https://images.unsplash.com/photo-1560180474-e8563fd75bab?w=400&q=80", description:"Tropical pineapple cream cake", tags:["pineapple","fruit cake","fresh"], status:"active" },
  { id:"p012", name:"Vanilla Cake (500g)", category:"cakes", brand:"Raj Confectionery", price:220, discountPrice:200, stock:"In Stock", quantity:15, image:"https://images.unsplash.com/photo-1555507036-ab1f4038808a?w=400&q=80", description:"Classic soft vanilla sponge cake", tags:["vanilla","simple","light"], status:"active" },

  // Namkeen
  { id:"p013", name:"Haldiram Bikaneri Bhujia 400g", category:"namkeen", brand:"Haldiram", price:90, discountPrice:80, stock:"In Stock", quantity:30, image:"https://images.unsplash.com/photo-1601050690117-94f5f7fa8b13?w=400&q=80", description:"Authentic Bikaner-style fine sev bhujia", tags:["bhujia","namkeen","haldiram"], status:"active" },
  { id:"p014", name:"Haldiram Khatta Meetha 200g", category:"namkeen", brand:"Haldiram", price:40, discountPrice:null, stock:"In Stock", quantity:40, image:"https://images.unsplash.com/photo-1559181567-c3190ef65ea3?w=400&q=80", description:"Sweet & tangy mixed namkeen snack", tags:["khatta meetha","sweet","salty"], status:"active" },
  { id:"p015", name:"Radhe Lal Kaju Mixture 250g", category:"namkeen", brand:"Radhe Lal", price:120, discountPrice:110, stock:"In Stock", quantity:20, image:"https://images.unsplash.com/photo-1571680322279-a226e6
