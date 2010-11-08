function(doc) {
    if (doc.doctype == "box") 
        emit(doc._id,doc);
}
