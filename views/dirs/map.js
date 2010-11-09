function(doc) {
    if (doc.doctype == "node" && doc.ftype=="dir")
        emit(doc.path+"/"+doc.name, doc);
}
