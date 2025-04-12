db = db.getSiblingDB('team1'); 

db.createUser({
  user: "Saphyiera",
  pwd: "team1top1",
  roles: [{ role: "readWrite", db: "team1" }]
});

db.createCollection('users');
